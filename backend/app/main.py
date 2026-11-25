"""API di Pulsar."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import llm
from .analysis.dossier import build_dossier
from .db_orm import SessionLocal, latest_edition, load_story, search_articles_in_db
from .pipeline import STORY_CACHE, build_stories, finalize_story, summarize
from .schemas import Article, Edition, SearchRequest, Story, StorySummary
from .sources import ORIENTATION_DISCLAIMER, SOURCE_NAMES, get_source, real_sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("pulsar.api")

app = FastAPI(
    title="Pulsar API",
    description="Informazione verificabile: fatti, interpretazioni e bias delle testate italiane.",
    version="2.0.0",
)

_origins = os.getenv("PULSAR_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_MODE = os.getenv("PULSAR_DEMO", "auto")  # auto | 1 | 0
JOBS: Dict[str, dict] = {}
_DEMO_EDITION: Optional[Edition] = None


def _demo_edition() -> Edition:
    global _DEMO_EDITION
    if _DEMO_EDITION is None:
        from .demo import build_demo_edition

        _DEMO_EDITION = build_demo_edition()
    return _DEMO_EDITION


# --------------------------------------------------------------------------
# Stato
# --------------------------------------------------------------------------


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm": llm.provider(),
        "embeddings": llm.embeddings_available(),
        "demo_mode": DEMO_MODE,
    }


# --------------------------------------------------------------------------
# Prima pagina
# --------------------------------------------------------------------------


@app.get("/api/edition", response_model=Edition)
def get_edition(demo: bool = False) -> Edition:
    if demo or DEMO_MODE == "1":
        return _demo_edition()
    with SessionLocal() as db:
        data = latest_edition(db, include_demo=False)
    if data:
        return Edition.model_validate(data)
    if DEMO_MODE == "auto":
        return _demo_edition()
    raise HTTPException(404, "Nessuna edizione ancora generata. Lancia POST /api/edition/refresh.")


def _run_job(job_id: str, fn):
    job = JOBS[job_id]
    job["status"] = "processing"
    try:
        result = fn(lambda msg: job.__setitem__("message", msg))
        job["result"] = result
        job["status"] = "completed"
        job["message"] = "Fatto"
    except Exception as e:  # pragma: no cover
        log.exception("Job %s fallito", job_id)
        job["status"] = "failed"
        job["message"] = str(e)


class JobResponse(BaseModel):
    job_id: str
    status: str


@app.post("/api/edition/refresh", response_model=JobResponse)
def refresh_edition(bg: BackgroundTasks) -> JobResponse:
    from .edition import build_edition

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "pending", "message": "In coda", "kind": "edition"}
    bg.add_task(_run_job, job_id, lambda p: (e := build_edition(progress=p)) and e.id)
    return JobResponse(job_id=job_id, status="pending")


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job non trovato")
    return {"job_id": job_id, "status": job["status"], "message": job.get("message")}


# --------------------------------------------------------------------------
# Ricerca per argomento
# --------------------------------------------------------------------------


class SearchStatus(BaseModel):
    job_id: str
    status: str
    message: Optional[str] = None
    stories: Optional[list[StorySummary]] = None


def _search(query: str, start_date: Optional[str], end_date: Optional[str], progress) -> list[StorySummary]:
    from .scrapers.news_scrapers import fetch_articles_from_all_sources

    progress("Cerco nell'archivio…")
    with SessionLocal() as db:
        rows = search_articles_in_db(db, query, start_date, end_date)
    archive = []
    for r in rows:
        src = get_source(r["source_id"])
        archive.append(
            Article(
                id=r["id"],
                source_id=r["source_id"],
                source_name=SOURCE_NAMES.get(r["source_id"], r["source_id"]),
                bias=r["bias"] or (src.leaning if src else "unknown"),
                bias_source=src.leaning if src else None,
                bias_article=r.get("bias_article"),
                bias_confidence=r.get("bias_confidence"),
                bias_explanation=r.get("bias_explanation"),
                orientation_score=r.get("orientation_score"),
                title=r["title"],
                snippet=r["snippet"] or "",
                body=r["body"],
                url=r["url"],
                published_at=r["published_at"],
                embedding=r.get("embedding"),
            )
        )

    progress("Cerco sulle testate…")
    try:
        live = fetch_articles_from_all_sources(query=query, start_date=start_date, end_date=end_date, max_pages=2, enrich_with_ai=False)
    except Exception as e:
        log.warning("Ricerca live fallita: %s", e)
        live = []

    merged = {a.url or a.id: a for a in archive}
    for a in live:
        merged[a.url or a.id] = a
    stories = build_stories(list(merged.values()), query=query, dossier_top_n=6, progress=progress)
    return [summarize(s) for s in stories]


@app.post("/api/search", response_model=JobResponse)
def search(payload: SearchRequest, bg: BackgroundTasks) -> JobResponse:
    q = payload.query.strip().lower()
    if not q:
        raise HTTPException(400, "Query vuota")
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "pending", "message": "Avvio ricerca…", "kind": "search"}
    bg.add_task(_run_job, job_id, lambda p: _search(q, payload.start_date, payload.end_date, p))
    return JobResponse(job_id=job_id, status="pending")


@app.get("/api/search/status/{job_id}", response_model=SearchStatus)
def search_status(job_id: str) -> SearchStatus:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job non trovato")
    return SearchStatus(
        job_id=job_id,
        status=job["status"],
        message=job.get("message"),
        stories=job.get("result") if job["status"] == "completed" else None,
    )


# --------------------------------------------------------------------------
# Storia
# --------------------------------------------------------------------------


@app.get("/api/story/{story_id}", response_model=Story)
def get_story(story_id: str) -> Story:
    story = STORY_CACHE.get(story_id)
    if story is None and story_id.startswith("demo-"):
        _demo_edition()
        story = STORY_CACHE.get(story_id)
    if story is None:
        with SessionLocal() as db:
            data = load_story(db, story_id)
        if data:
            story = Story.model_validate(data)
            STORY_CACHE[story_id] = story
    if story is None:
        raise HTTPException(404, "Storia non trovata")
    if story.dossier is None and llm.available() and len({a.source_id for a in story.articles}) >= 2:
        story.dossier = build_dossier(story.articles)
        finalize_story(story, with_dossier=False)
    return story


# --------------------------------------------------------------------------
# Trasparenza
# --------------------------------------------------------------------------


@app.get("/api/sources")
def sources(demo: bool = False) -> dict:
    from .edition import LAST_HEALTH

    health = {h.source_id: {"ok": h.ok, "entries": h.entries, "error": h.error} for h in LAST_HEALTH}
    items = real_sources()
    if demo or DEMO_MODE == "1":
        from .demo import DEMO_SOURCES

        items = DEMO_SOURCES
    return {
        "disclaimer": ORIENTATION_DISCLAIMER,
        "updated": "2026-11",
        "sources": [{**s.to_dict(), "health": health.get(s.id)} for s in sorted(items, key=lambda s: s.orientation)],
    }
