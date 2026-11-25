"""L'aggregatore: un giro completo, ripetuto a intervalli.

    python -m app.aggregator.worker            # un giro
    python -m app.aggregator.worker --every 20 # un giro ogni 20 minuti

Fasi di un giro (ognuna cronometrata e registrata in ``runs``):
  fetch -> normalizza/deduplica -> arricchisci -> aggancia/raggruppa
  -> verifica (dossier) -> pubblica l'edizione

Ogni fase isola i propri errori: una testata rotta, un articolo illeggibile o
un dossier fallito non fermano il giro. Se una fase intera fallisce, il giro
viene registrato come fallito e l'edizione precedente resta online.
"""

from __future__ import annotations

import argparse
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from ..db_orm import (
    RunLog,
    SessionLocal,
    active_story_records,
    deactivate_stale_stories,
    save_edition,
    save_story,
)
from ..pipeline import STORY_CACHE, assemble_edition, enrich
from ..schemas import Edition, Story
from ..sources import real_sources
from .feeds import fetch_all
from .normalize import normalize_and_dedupe
from .tracker import WINDOW_HOURS, signature, update_stories

log = logging.getLogger("pulsar.worker")
_LOCK = threading.Lock()
MAX_AGE_HOURS = 36


class Run:
    def __init__(self, progress: Callable[[str], None]):
        self.id = str(uuid.uuid4())
        self.started = datetime.utcnow()
        self.stages: dict = {}
        self.counts: dict = {}
        self.errors: List[str] = []
        self.progress = progress
        self._t = time.monotonic()

    def stage(self, name: str, message: str):
        now = time.monotonic()
        if self.stages:
            last = list(self.stages)[-1]
            self.stages[last] = round(now - self._t, 2)
        self.stages[name] = None
        self._t = now
        self.progress(message)

    def close(self, ok: bool):
        if self.stages:
            last = list(self.stages)[-1]
            self.stages[last] = round(time.monotonic() - self._t, 2)
        with SessionLocal() as db:
            db.merge(
                RunLog(
                    id=self.id,
                    started_at=self.started,
                    finished_at=datetime.utcnow(),
                    ok=ok,
                    data={"stages": self.stages, "counts": self.counts, "errors": self.errors[:50]},
                )
            )
            db.commit()


def load_open_stories(now: datetime) -> List[Story]:
    with SessionLocal() as db:
        recs = active_story_records(db, now - timedelta(hours=WINDOW_HOURS))
        out = []
        for r in recs:
            try:
                out.append(Story.model_validate(r.data))
            except Exception as e:  # pragma: no cover
                log.warning("Storia %s illeggibile: %s", r.id, e)
        return out


def run_once(progress: Callable[[str], None] = lambda _: None, sources=None, fetch_bodies: bool = True) -> Optional[Edition]:
    if not _LOCK.acquire(blocking=False):
        progress("Un giro è già in corso.")
        return None
    run = Run(progress)
    ok = False
    try:
        now = datetime.utcnow()
        sources = sources or real_sources()

        run.stage("fetch", "Leggo i feed delle testate…")
        results = fetch_all(sources)
        raw = [a for r in results for a in r.articles]
        cutoff = now - timedelta(hours=MAX_AGE_HOURS)
        raw = [a for a in raw if not a.published_at or a.published_at >= cutoff]
        run.counts["feeds"] = {k: sum(1 for r in results if r.status == k) for k in ("ok", "not_modified", "skipped", "error")}
        run.errors += [f"{r.source_id}: {r.error}" for r in results if r.status == "error"]

        run.stage("normalize", "Tolgo doppioni e rubriche…")
        articles, dropped = normalize_and_dedupe(raw)
        run.counts["raw"], run.counts["unique"], run.counts["dropped"] = len(raw), len(articles), dropped

        open_stories = load_open_stories(now)
        known = {a.id for s in open_stories for a in s.articles}
        fresh = [a for a in articles if a.id not in known]
        run.counts["fresh"] = len(fresh)

        run.stage("enrich", f"Leggo {len(fresh)} articoli nuovi…")
        with ThreadPoolExecutor(max_workers=6) as ex:
            fresh = list(ex.map(lambda a: enrich(a, None, fetch_bodies), fresh))

        run.stage("track", "Aggancio gli articoli alle storie e verifico i fatti…")
        touched, counts = update_stories(open_stories, fresh, now)
        run.counts.update(counts)

        run.stage("publish", "Pubblico l'edizione…")
        with SessionLocal() as db:
            for s in touched:
                save_story(db, s, signature=signature(s), active=True)
                STORY_CACHE[s.id] = s
            run.counts["closed_stories"] = deactivate_stale_stories(db, now - timedelta(hours=WINDOW_HOURS))
        current = load_open_stories(now)
        for s in current:
            STORY_CACHE[s.id] = s
        current.sort(key=lambda s: s.score, reverse=True)
        healthy = {r.source_id for r in results if r.status in ("ok", "not_modified")}
        edition = assemble_edition(current, demo=False, sources_ok=len(healthy), sources_total=len({s.id for s in sources}))
        if edition.stories:
            with SessionLocal() as db:
                save_edition(db, edition)
        else:
            run.errors.append("Nessuna storia: edizione non pubblicata, resta la precedente.")
        ok = True
        return edition
    except Exception as e:
        log.exception("Giro fallito")
        run.errors.append(f"giro fallito: {e}")
        return None
    finally:
        run.close(ok)
        _LOCK.release()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    p = argparse.ArgumentParser(description="Aggregatore Pulsar")
    p.add_argument("--every", type=int, default=0, help="minuti tra un giro e l'altro (0 = un giro solo)")
    args = p.parse_args()
    while True:
        e = run_once(progress=lambda m: log.info(m))
        if e:
            log.info("Edizione %s: %d storie, %d articoli", e.id, len(e.stories), e.articles_analyzed)
        if not args.every:
            break
        time.sleep(args.every * 60)


if __name__ == "__main__":
    main()
