"""Tracciamento incrementale delle storie.

Una notizia non nasce completa: all'inizio c'e' un lancio d'agenzia, poi
arrivano le altre testate, poi le smentite. Per questo le storie hanno un ID
stabile e vengono *aggiornate* a ogni giro invece di essere ricreate:

1. gli articoli nuovi vengono agganciati alla storia aperta piu' simile
   (similarita' con il centroide, solo storie delle ultime 72 ore);
2. quelli che non somigliano a niente vengono raggruppati tra loro in storie nuove;
3. il dossier viene rigenerato solo se e' cambiato qualcosa che conta
   (nuove testate, o almeno due articoli nuovi), per non bruciare chiamate al
   modello e per tenere stabili gli stati;
4. quando un fatto cambia stato tra una versione e l'altra del dossier
   ("riportato" -> "confermato"), lo registriamo negli aggiornamenti della storia.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

from .. import llm
from ..analysis.dossier import build_dossier
from ..analysis.metrics import compute_metrics, story_score
from ..clustering import ITALIAN_STOPWORDS, _compute_stats, cluster_articles_into_stories
from ..schemas import Article, Dossier, Story, StoryUpdate
from ..topics import assign_topics

log = logging.getLogger("pulsar.tracker")

WINDOW_HOURS = int(os.getenv("PULSAR_STORY_WINDOW_HOURS", "72"))
ATTACH_TFIDF = float(os.getenv("PULSAR_ATTACH_TFIDF", "0.30"))
ATTACH_EMB = float(os.getenv("PULSAR_ATTACH_EMB", "0.72"))
DOSSIER_MIN_AGE_MIN = 20


def signature(story: Story) -> str:
    return hashlib.md5("|".join(sorted(a.id for a in story.articles)).encode()).hexdigest()


def _naive(ts: Optional[datetime]) -> Optional[datetime]:
    return ts.replace(tzinfo=None) if ts and ts.tzinfo else ts


def _doc(a: Article) -> str:
    return f"{a.title} {a.title} {a.snippet} {(a.body or '')[:600]}"


def _vectors(docs: List[Article]) -> Tuple[np.ndarray, bool]:
    """Embedding se disponibili per tutti, altrimenti TF-IDF."""
    if docs and all(a.embedding for a in docs):
        X = np.array([a.embedding for a in docs], dtype=float)
        return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9), True
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = TfidfVectorizer(stop_words=list(ITALIAN_STOPWORDS), sublinear_tf=True, strip_accents="unicode")
    X = vec.fit_transform([_doc(a) for a in docs]).toarray()
    return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9), False


def attach(open_stories: List[Story], new: List[Article], now: datetime) -> Tuple[Dict[str, List[Article]], List[Article]]:
    """Assegna gli articoli nuovi alle storie aperte. Restituisce
    {story_id: [articoli agganciati]} e gli articoli rimasti orfani."""
    if not open_stories or not new:
        return {}, list(new)
    window = now - timedelta(hours=WINDOW_HOURS)
    candidates = [s for s in open_stories if (_naive(s.stats.last_published_at) or now) >= window]
    if not candidates:
        return {}, list(new)

    pool = [a for s in candidates for a in s.articles] + new
    X, is_emb = _vectors(pool)
    threshold = ATTACH_EMB if is_emb else ATTACH_TFIDF
    offsets, i = [], 0
    for s in candidates:
        offsets.append((i, i + len(s.articles)))
        i += len(s.articles)
    centroids = np.array([X[a:b].mean(axis=0) for a, b in offsets])
    centroids /= np.linalg.norm(centroids, axis=1, keepdims=True) + 1e-9

    attached: Dict[str, List[Article]] = {}
    orphans: List[Article] = []
    for j, art in enumerate(new):
        sims = centroids @ X[i + j]
        best = int(np.argmax(sims))
        if sims[best] >= threshold:
            attached.setdefault(candidates[best].id, []).append(art)
        else:
            orphans.append(art)
    return attached, orphans


def _tok(text: str) -> set:
    return {w for w in re.findall(r"[a-zà-ù0-9]+", text.lower()) if len(w) > 3}


def fact_changes(old: Optional[Dossier], new: Optional[Dossier]) -> List[StoryUpdate]:
    """Confronta due versioni del dossier: quali fatti hanno cambiato stato, quali sono nuovi."""
    if not old or not new:
        return []
    out = []
    for f in new.facts:
        ft = _tok(f.text)
        best, best_sim = None, 0.0
        for g in old.facts:
            gt = _tok(g.text)
            sim = len(ft & gt) / (len(ft | gt) or 1)
            if sim > best_sim:
                best, best_sim = g, sim
        if best and best_sim >= 0.5:
            if best.status != f.status:
                out.append(
                    StoryUpdate(
                        kind="cambio_stato",
                        text=f"«{f.text}» passa da {best.status.replace('_', ' ')} a {f.status.replace('_', ' ')}.",
                        fact_text=f.text,
                        from_status=best.status,
                        to_status=f.status,
                    )
                )
        else:
            out.append(StoryUpdate(kind="nuovo_fatto", text=f"Nuovo fatto: «{f.text}» ({f.status.replace('_', ' ')}).", fact_text=f.text, to_status=f.status))
    return out


def needs_dossier(story: Story, prev_outlets: set, prev_count: int, now: datetime) -> bool:
    outlets = {a.source_id for a in story.articles}
    if len(outlets) < 2 or not llm.available():
        return False
    if story.dossier is None:
        return True
    age = now - (_naive(story.dossier.generated_at) or now)
    if age < timedelta(minutes=DOSSIER_MIN_AGE_MIN):
        return False
    return outlets != prev_outlets or len(story.articles) - prev_count >= 2


def refresh_story(story: Story, prev_outlets: set, prev_count: int, now: datetime, regenerate: bool = True) -> Story:
    story.stats = _compute_stats(story.articles)
    story.metrics = compute_metrics(story)
    if regenerate and needs_dossier(story, prev_outlets, prev_count, now):
        new = build_dossier(story.articles)
        if new:
            story.updates += fact_changes(story.dossier, new)
            story.dossier = new
    if story.dossier:
        story.title = story.dossier.neutral_title or story.title
        story.section = story.dossier.section or story.section
        story.metrics = compute_metrics(story)
    story.topics = assign_topics(story)
    story.score = story_score(story, now)
    story.updates = story.updates[-30:]
    return story


def update_stories(open_stories: List[Story], new: List[Article], now: Optional[datetime] = None, regenerate: bool = True) -> Tuple[List[Story], dict]:
    """Applica un giro di articoli nuovi. Restituisce le storie toccate e i conteggi."""
    now = now or datetime.utcnow()
    known = {a.id for s in open_stories for a in s.articles}
    new = [a for a in new if a.id not in known]
    by_id = {s.id: s for s in open_stories}

    attached, orphans = attach(open_stories, new, now)
    touched: List[Story] = []
    for sid, arts in attached.items():
        s = by_id[sid]
        prev_outlets, prev_count = {a.source_id for a in s.articles}, len(s.articles)
        s.articles.extend(arts)
        added_outlets = {a.source_id for a in arts} - prev_outlets
        if added_outlets:
            names = sorted({a.source_name for a in arts if a.source_id in added_outlets})
            s.updates.append(StoryUpdate(kind="nuove_testate", text=f"Ne parlano anche: {', '.join(names)}."))
        else:
            s.updates.append(StoryUpdate(kind="nuovi_articoli", text=f"{len(arts)} nuovi articoli."))
        touched.append(refresh_story(s, prev_outlets, prev_count, now, regenerate))

    created = []
    for s in cluster_articles_into_stories("", orphans):
        s.id = str(uuid.uuid4())
        s.updates = [StoryUpdate(kind="apertura", text=f"Prima notizia da {s.articles[-1].source_name}.")]
        created.append(refresh_story(s, set(), 0, now, regenerate))

    return touched + created, {"new_articles": len(new), "attached": sum(len(v) for v in attached.values()), "new_stories": len(created), "updated_stories": len(touched)}
