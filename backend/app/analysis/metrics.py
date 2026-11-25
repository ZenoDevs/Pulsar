"""Metriche deterministiche di copertura: spettro, punti ciechi, cronologia."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import List, Optional

from ..schemas import (
    Article,
    Blindspot,
    Dossier,
    Independence,
    SpectrumPoint,
    Story,
    StoryMetrics,
    TimelineEntry,
)
from ..sources import get_source, leaning_from_score
from .independence import detect_echoes, independence_summary

BLINDSPOT_MIN_OUTLETS = 3
BLINDSPOT_SHARE = 0.8


def _orientation(a: Article) -> Optional[float]:
    if a.orientation_score is not None:
        return a.orientation_score
    s = get_source(a.source_id)
    return s.orientation if s else None


def spectrum(articles: List[Article]) -> List[SpectrumPoint]:
    by_src = defaultdict(list)
    for a in articles:
        by_src[a.source_id].append(a)
    pts = []
    for sid, arts in by_src.items():
        src = get_source(sid)
        if not src:
            continue
        pts.append(
            SpectrumPoint(
                source_id=sid,
                source_name=src.name,
                orientation=src.orientation,
                articles=len(arts),
            )
        )
    return sorted(pts, key=lambda p: p.orientation)


def leaning_share(articles: List[Article]) -> dict:
    """Quota per fascia, pesata per *testata* (non per articolo): una testata
    che pubblica dieci pezzi non deve spostare lo spettro da sola."""
    outlets = {}
    for a in articles:
        s = get_source(a.source_id)
        outlets[a.source_id] = s.leaning if s else a.bias
    c = Counter(outlets.values())
    n = sum(c[k] for k in ("left", "center", "right")) or 1
    return {k: round(c.get(k, 0) / n, 3) for k in ("left", "center", "right")}


def detect_blindspot(articles: List[Article]) -> Optional[Blindspot]:
    outlets = {a.source_id for a in articles}
    if len(outlets) < BLINDSPOT_MIN_OUTLETS:
        return None
    share = leaning_share(articles)
    if share["right"] == 0 and share["left"] >= 0.5:
        return Blindspot(
            side="right",
            message="Coperta quasi solo da testate di sinistra e centro: chi legge giornali di destra probabilmente non l'ha vista.",
        )
    if share["left"] == 0 and share["right"] >= 0.5:
        return Blindspot(
            side="left",
            message="Coperta quasi solo da testate di destra e centro: chi legge giornali di sinistra probabilmente non l'ha vista.",
        )
    if share["left"] >= BLINDSPOT_SHARE:
        return Blindspot(side="right", message="Raccontata soprattutto a sinistra.")
    if share["right"] >= BLINDSPOT_SHARE:
        return Blindspot(side="left", message="Raccontata soprattutto a destra.")
    return None


def timeline(articles: List[Article]) -> List[TimelineEntry]:
    def key(a: Article):
        ts = a.published_at
        if ts is None:
            return datetime.max
        return ts.replace(tzinfo=None) if ts.tzinfo else ts

    return [
        TimelineEntry(
            article_id=a.id,
            source_id=a.source_id,
            source_name=a.source_name,
            title=a.title,
            published_at=a.published_at,
            is_echo=bool(a.echo_of),
        )
        for a in sorted(articles, key=key)
    ]


def solidity(dossier: Optional[Dossier]) -> tuple[Optional[float], dict]:
    if not dossier:
        return None, {}
    counts = Counter(f.status for f in dossier.facts)
    total = len(dossier.facts)
    counts["interpretazione"] = len(dossier.interpretations)
    if total == 0:
        return None, dict(counts)
    return round(counts.get("confermato", 0) / total, 3), dict(counts)


def compute_metrics(story: Story) -> StoryMetrics:
    arts = story.articles
    detect_echoes(arts)
    ind = independence_summary(arts)
    orients = [o for o in (_orientation(a) for a in arts) if o is not None]
    tl = timeline(arts)
    first = next((t for t in tl if t.published_at), None)
    sol, counts = solidity(story.dossier)
    return StoryMetrics(
        spectrum=spectrum(arts),
        leaning_share=leaning_share(arts),
        mean_orientation=round(sum(orients) / len(orients), 3) if orients else None,
        independence=Independence(**ind),
        blindspot=detect_blindspot(arts),
        solidity=sol,
        status_counts=counts,
        first_reported_by=first.source_name if first else None,
        timeline=tl,
    )


def story_score(story: Story, now: Optional[datetime] = None) -> float:
    """Importanza per la prima pagina: ampiezza > volume, con decadimento."""
    m = story.metrics
    if not m:
        return float(len(story.articles))
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    last = story.stats.last_published_at
    if last is not None and last.tzinfo:
        last = last.replace(tzinfo=None)
    hours = max(0.0, (now - last).total_seconds() / 3600) if last else 24.0
    decay = 0.5 ** (hours / 18)  # dimezza ogni 18 ore
    breadth = m.independence.independent_voices * 2 + m.independence.outlets
    sides = sum(1 for v in m.leaning_share.values() if v > 0)
    return round((breadth + sides * 1.5) * (0.35 + 0.65 * decay), 3)


__all__ = ["compute_metrics", "story_score", "leaning_from_score"]
