"""API di Pulsar."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import llm
from .analysis.dossier import build_dossier
from .db_orm import SessionLocal, latest_edition, load_story, search_articles_in_db
from .pipeline import STORY_CACHE, build_stories, finalize_story, summarize
from .schemas import Article, Edition, SearchRequest, Story, StorySummary
from .topics import CATALOG, expand_custom, personalize
from .ratelimit import limit
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
SCHEDULE_MINUTES = int(os.getenv("PULSAR_SCHEDULE_MINUTES", "0"))
JOBS: Dict[str, dict] = {}
_DEMO_EDITION: Optional[Edition] = None


def _demo_edition() -> Edition:
    global _DEMO_EDITION
    if _DEMO_EDITION is None:
        from .demo import build_demo_edition

        _DEMO_EDITION = build_demo_edition()
    return _DEMO_EDITION


@app.on_event("startup")
def _start_scheduler() -> None:
    """Aggregatore dentro il processo API (comodo in sviluppo e su un solo server).
    In produzione meglio un processo separato: python -m app.aggregator.worker --every 20"""
    if SCHEDULE_MINUTES <= 0:
        return
    import threading
    import time

    from .aggregator.worker import run_once

    def loop():
        while True:
            run_once(progress=lambda m: log.info(m))
            time.sleep(SCHEDULE_MINUTES * 60)

    threading.Thread(target=loop, daemon=True, name="pulsar-aggregator").start()


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
# Personalizzazione
# --------------------------------------------------------------------------


@app.get("/api/topics")
def topics() -> dict:
    return {"topics": [{"id": t.id, "label": t.label, "blurb": t.blurb} for t in CATALOG]}


@app.get("/api/topics/expand")
def topics_expand(q: str) -> dict:
    q = q.strip()[:60]
    if not q:
        raise HTTPException(400, "Argomento vuoto")
    return {"label": q, "keywords": expand_custom(q)}


class FeedRequest(BaseModel):
    topics: list[dict] = []
    seen: list[str] = []
    more: list[str] = []
    less: list[str] = []
    sections: dict[str, float] = {}
    demo: bool = False


@app.post("/api/feed")
def feed(req: FeedRequest) -> dict:
    """Edizione personalizzata: stessa base per tutti, ordine e binari per te.
    Il profilo arriva dal browser e non viene salvato."""
    edition = get_edition(demo=req.demo)
    pool = edition.stories + [b for b in edition.blindspots if b.id not in {s.id for s in edition.stories}]
    result = personalize(pool, req.model_dump())
    return {
        "edition": edition.model_copy(update={"stories": []}),
        "for_you": result["for_you"],
        "rails": result["rails"],
        "blindspots": edition.blindspots,
    }


# --------------------------------------------------------------------------
# Verifica, domande, storie seguite, audio
# --------------------------------------------------------------------------


class CheckRequest(BaseModel):
    claim: str
    demo: bool = False


@app.post("/api/check")
def check(req: CheckRequest, request: Request):
    """Verifica un'affermazione contro le storie correnti."""
    from .analysis.qa import check_claim
    from .store import current_stories

    limit(request, "check", per_minute=20)
    claim = req.claim.strip()
    if len(claim) < 8:
        raise HTTPException(400, "Scrivi una frase un po' più lunga: almeno qualche parola.")
    demo = req.demo or DEMO_MODE == "1" or (DEMO_MODE == "auto" and not _has_real_edition())
    return check_claim(claim, current_stories(demo))


class AskRequest(BaseModel):
    question: str


@app.post("/api/story/{story_id}/ask")
def ask(story_id: str, req: AskRequest, request: Request):
    from .analysis.qa import ask_story

    limit(request, "ask", per_minute=20)
    if len(req.question.strip()) < 4:
        raise HTTPException(400, "Scrivi una domanda.")
    story = get_story(story_id)
    return ask_story(story, req.question)


class UpdatesRequest(BaseModel):
    follow: dict[str, Optional[str]] = {}
    demo: bool = False


@app.post("/api/stories/updates")
def story_updates(req: UpdatesRequest) -> dict:
    """Le storie che segui: cosa e' cambiato dall'ultima volta che le hai aperte."""
    out = []
    for sid, since in list(req.follow.items())[:50]:
        try:
            story = get_story(sid)
        except HTTPException:
            out.append({"id": sid, "gone": True})
            continue
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                since_dt = None
        new = [u for u in story.updates if since_dt is None or (u.at.replace(tzinfo=None) if u.at.tzinfo else u.at) > since_dt]
        latest = max((u.at for u in story.updates), default=None)
        out.append(
            {
                "id": story.id,
                "title": story.title,
                "section": story.section,
                "status_counts": story.metrics.status_counts if story.metrics else {},
                "new_updates": [u.model_dump() for u in new][-5:],
                "latest_update_at": latest,
            }
        )
    out.sort(key=lambda x: -len(x.get("new_updates") or []))
    return {"stories": out}


class TTSRequest(BaseModel):
    text: str


@app.post("/api/tts")
def tts(req: TTSRequest, request: Request):
    """Voce del briefing con ElevenLabs, se configurato. Senza chiave risponde 404
    e il frontend usa la sintesi vocale del browser."""
    import requests as _rq
    from fastapi import Response

    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise HTTPException(404, "Voce di ElevenLabs non configurata")
    limit(request, "tts", per_minute=6)
    text = req.text.strip()[:4500]
    voice = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
    model = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    r = _rq.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json={"text": text, "model_id": model, "language_code": "it"},
        timeout=60,
    )
    if r.status_code != 200:
        raise HTTPException(502, f"ElevenLabs ha risposto {r.status_code}")
    return Response(content=r.content, media_type="audio/mpeg")


def _has_real_edition() -> bool:
    with SessionLocal() as db:
        return latest_edition(db, include_demo=False) is not None


# --------------------------------------------------------------------------
# Trasparenza
# --------------------------------------------------------------------------


@app.get("/api/status")
def status() -> dict:
    """Salute dell'aggregatore: ultimi giri, stato di ogni feed."""
    from .db_orm import FeedState, RunLog

    with SessionLocal() as db:
        runs = db.query(RunLog).order_by(RunLog.started_at.desc()).limit(10).all()
        feeds = db.query(FeedState).all()
        return {
            "llm": llm.provider(),
            "embeddings": llm.embeddings_available(),
            "schedule_minutes": SCHEDULE_MINUTES,
            "runs": [
                {"id": r.id, "started_at": r.started_at, "finished_at": r.finished_at, "ok": r.ok, **(r.data or {})}
                for r in runs
            ],
            "feeds": [
                {
                    "source_id": f.source_id,
                    "url": f.url,
                    "healthy": (f.consecutive_failures or 0) == 0,
                    "consecutive_failures": f.consecutive_failures,
                    "paused_until": f.open_until,
                    "last_ok_at": f.last_ok_at,
                    "last_error": f.last_error,
                    "last_entries": f.last_entries,
                }
                for f in sorted(feeds, key=lambda f: (-(f.consecutive_failures or 0), f.source_id or ""))
            ],
        }



@app.get("/api/sources")
def sources(demo: bool = False) -> dict:
    from .db_orm import FeedState

    with SessionLocal() as db:
        health = {
            f.source_id: {"ok": (f.consecutive_failures or 0) == 0, "entries": f.last_entries, "error": f.last_error}
            for f in db.query(FeedState).all()
        }
    items = real_sources()
    if demo or DEMO_MODE == "1":
        from .demo import DEMO_SOURCES

        items = DEMO_SOURCES
    return {
        "disclaimer": ORIENTATION_DISCLAIMER,
        "updated": "2026-11",
        "sources": [{**s.to_dict(), "health": health.get(s.id)} for s in sorted(items, key=lambda s: s.orientation)],
    }


# --------------------------------------------------------------------------
# Frontend statico (produzione): stesso server, stessa origine
# --------------------------------------------------------------------------

_STATIC = os.getenv("PULSAR_STATIC_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.isdir(_STATIC):
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=os.path.join(_STATIC, "assets")), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        """File pubblici se esistono, altrimenti l'app (che gestisce le sue rotte e il 404)."""
        if path.startswith("api/"):
            raise HTTPException(404, "Endpoint inesistente")
        candidate = os.path.normpath(os.path.join(_STATIC, path))
        if path and candidate.startswith(os.path.normpath(_STATIC)) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_STATIC, "index.html"), headers={"Cache-Control": "no-cache"})
