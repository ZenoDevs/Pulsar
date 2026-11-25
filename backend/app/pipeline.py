"""Pipeline comune: articoli -> storie con metriche e dossier.

Usata sia dalla prima pagina (feed RSS) sia dalla ricerca per argomento.
"""

from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable, Dict, List, Optional

from . import llm
from .analysis.dossier import build_dossier
from .analysis.metrics import compute_metrics, story_score
from .clustering import cluster_articles_into_stories
from .db_orm import SessionLocal, get_article_by_url, save_article, save_story
from .ingest.rss import extract_full_text
from .schemas import Article, Edition, Headline, Story, StorySummary
from .sources import get_source
from .services.openai_service import enrich_article_smart, fuse_bias

log = logging.getLogger("pulsar.pipeline")

# Cache in memoria (la fonte di verita' e' il DB)
STORY_CACHE: Dict[str, Story] = {}

Progress = Callable[[str], None]


def _noop(_: str) -> None:
    pass


def enrich(article: Article, query: Optional[str] = None, fetch_body: bool = True) -> Article:
    with SessionLocal() as db:
        if article.url:
            existing = get_article_by_url(db, article.url)
            if existing and existing.get("body"):
                article.body = existing["body"]
        if fetch_body and not article.body and article.url:
            article.body = extract_full_text(article.url)
        if article.url:
            save_article(
                db,
                {
                    "id": article.id,
                    "url": article.url,
                    "source_id": article.source_id,
                    "title": article.title,
                    "snippet": article.snippet,
                    "body": article.body,
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                },
                query=query,
            )
        try:
            return enrich_article_smart(article, db=db)
        except Exception as e:
            log.warning("Arricchimento fallito per %s: %s", article.url, e)
            fuse_bias(article)
            return article


def finalize_story(story: Story, with_dossier: bool) -> Story:
    story.metrics = compute_metrics(story)
    if with_dossier and story.dossier is None:
        story.dossier = build_dossier(story.articles)
    if story.dossier:
        story.title = story.dossier.neutral_title or story.title
        story.section = story.dossier.section or story.section
        story.metrics = compute_metrics(story)  # aggiorna la solidita'
    from .topics import assign_topics

    story.topics = assign_topics(story)
    story.score = story_score(story)
    return story


def build_stories(
    articles: List[Article],
    query: str = "",
    dossier_top_n: int = 12,
    fetch_bodies: bool = True,
    progress: Progress = _noop,
) -> List[Story]:
    if not articles:
        return []

    progress(f"Leggo e analizzo {len(articles)} articoli…")
    with ThreadPoolExecutor(max_workers=6) as ex:
        articles = list(ex.map(lambda a: enrich(a, query or None, fetch_bodies), articles))

    progress("Raggruppo gli articoli per fatto…")
    stories = cluster_articles_into_stories(query, articles)

    for s in stories:
        s.metrics = compute_metrics(s)
        s.score = story_score(s)
    stories.sort(key=lambda s: s.score, reverse=True)

    # Dossier solo dove c'e' qualcosa da confrontare: almeno due testate
    candidates = [s for s in stories if len({a.source_id for a in s.articles}) >= 2][:dossier_top_n]
    if llm.available() and candidates:
        progress(f"Verifico i fatti di {len(candidates)} storie…")
        with ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(lambda s: finalize_story(s, True), candidates))

    for s in stories:
        if s.metrics is None:
            finalize_story(s, False)
    stories.sort(key=lambda s: s.score, reverse=True)

    with SessionLocal() as db:
        for s in stories:
            STORY_CACHE[s.id] = s
            try:
                save_story(db, s)
            except Exception as e:
                log.warning("Salvataggio storia fallito: %s", e)
    return stories


def summarize(story: Story) -> StorySummary:
    d = story.dossier
    key = []
    if d:
        order = {"confermato": 0, "contestato": 1, "riportato": 2, "non_verificato": 3}
        key = sorted(d.facts, key=lambda f: order.get(f.status, 9))[:3]
    headlines = []
    seen = set()
    for a in sorted(story.articles, key=lambda a: (bool(a.echo_of), a.published_at is None)):
        src = get_source(a.source_id)
        if not src or a.source_id in seen:
            continue
        seen.add(a.source_id)
        headlines.append(
            Headline(source_id=a.source_id, source_name=src.name, orientation=src.orientation, title=a.title, url=a.url)
        )
    headlines.sort(key=lambda h: h.orientation)
    image = next((a.image_url for a in story.articles if a.image_url), None)
    return StorySummary(
        id=story.id,
        headlines=headlines,
        loaded_terms=d.loaded_language[:3] if d else [],
        image_url=image,
        topics=story.topics,
        updates=story.updates[-3:],
        title=story.title,
        summary=d.summary if d else (story.articles[0].snippet if story.articles else None),
        section=story.section,
        stats=story.stats,
        metrics=story.metrics,
        key_facts=key,
        top_divergence=d.divergences[0] if d and d.divergences else None,
        score=story.score,
    )


def assemble_edition(stories: List[Story], *, demo: bool, sources_ok: int, sources_total: int) -> Edition:
    multi = [s for s in stories if len({a.source_id for a in s.articles}) >= 2]
    front = multi[:30] or stories[:30]
    blind = [s for s in multi if s.metrics and s.metrics.blindspot][:8]
    return Edition(
        id=str(uuid.uuid4()),
        generated_at=datetime.utcnow(),
        demo=demo,
        sources_ok=sources_ok,
        sources_total=sources_total,
        articles_analyzed=sum(len(s.articles) for s in stories),
        stories=[summarize(s) for s in front],
        blindspots=[summarize(s) for s in blind],
    )
