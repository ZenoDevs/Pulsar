"""La prima pagina: feed RSS -> storie -> edizione."""

from __future__ import annotations

import logging
from typing import Callable, List, Optional

from .db_orm import SessionLocal, save_edition
from .ingest.rss import FeedHealth, fetch_all
from .pipeline import assemble_edition, build_stories
from .schemas import Edition

log = logging.getLogger("pulsar.edition")

LAST_HEALTH: List[FeedHealth] = []


def build_edition(
    progress: Callable[[str], None] = lambda _: None,
    max_age_hours: int = 36,
    dossier_top_n: int = 12,
) -> Optional[Edition]:
    global LAST_HEALTH
    progress("Leggo i feed delle testate…")
    articles, health = fetch_all(max_age_hours=max_age_hours)
    LAST_HEALTH = health
    sources_ok = len({h.source_id for h in health if h.ok})
    sources_total = len({h.source_id for h in health})
    if not articles:
        log.warning("Nessun articolo dai feed: edizione non generata")
        return None

    stories = build_stories(articles, query="", dossier_top_n=dossier_top_n, progress=progress)
    edition = assemble_edition(stories, demo=False, sources_ok=sources_ok, sources_total=sources_total)
    with SessionLocal() as db:
        save_edition(db, edition)
    return edition
