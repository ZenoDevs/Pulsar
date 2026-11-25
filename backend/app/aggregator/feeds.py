"""Lettura affidabile dei feed.

- GET condizionali (ETag / Last-Modified): se il feed non e' cambiato, il
  server risponde 304 e non riscarichiamo nulla.
- Retry con backoff esponenziale sugli errori transitori (timeout, 5xx, 429).
- Circuit breaker per feed: dopo N fallimenti consecutivi il feed viene messo
  in pausa per un tempo crescente, cosi' una testata rotta non rallenta il giro
  e non la martelliamo di richieste.
- Lo stato e' salvato su DB, quindi sopravvive ai riavvii ed e' visibile in
  /api/status.
"""

from __future__ import annotations

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

import requests

from ..db_orm import FeedState, SessionLocal
from ..ingest.rss import HEADERS, TIMEOUT, parse_feed
from ..schemas import Article
from ..sources import SourceInfo

log = logging.getLogger("pulsar.feeds")

BREAKER_THRESHOLD = 3  # fallimenti consecutivi prima di aprire il circuito
BREAKER_BASE_MINUTES = 15  # pausa iniziale, raddoppia a ogni apertura
BREAKER_MAX_HOURS = 12
RETRIES = 2


@dataclass
class FetchResult:
    source_id: str
    url: str
    status: str  # ok | not_modified | skipped | error | empty
    articles: List[Article] = field(default_factory=list)
    error: Optional[str] = None
    elapsed_ms: int = 0


def _get_with_retry(url: str, headers: dict) -> requests.Response:
    last: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            r = requests.get(url, headers=headers, timeout=TIMEOUT)
            if r.status_code in (429, 500, 502, 503, 504) and attempt < RETRIES:
                retry_after = r.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else 1.5 * 2**attempt
                time.sleep(min(wait, 10) + random.uniform(0, 0.5))
                continue
            return r
        except (requests.Timeout, requests.ConnectionError) as e:
            last = e
            if attempt < RETRIES:
                time.sleep(1.5 * 2**attempt + random.uniform(0, 0.5))
    raise last or RuntimeError("richiesta fallita")


def breaker_pause(failures: int) -> timedelta:
    opens = max(0, failures - BREAKER_THRESHOLD)
    minutes = min(BREAKER_BASE_MINUTES * 2**opens, BREAKER_MAX_HOURS * 60)
    return timedelta(minutes=minutes)


def fetch_one(source: SourceInfo, url: str, now: Optional[datetime] = None) -> FetchResult:
    now = now or datetime.utcnow()
    t0 = time.monotonic()
    with SessionLocal() as db:
        state = db.get(FeedState, url) or FeedState(url=url, source_id=source.id, consecutive_failures=0)
        if state.open_until and state.open_until > now:
            return FetchResult(source.id, url, "skipped", error=f"in pausa fino alle {state.open_until:%H:%M} UTC")

        headers = dict(HEADERS)
        if state.etag:
            headers["If-None-Match"] = state.etag
        if state.last_modified:
            headers["If-Modified-Since"] = state.last_modified

        state.last_checked_at = now
        try:
            r = _get_with_retry(url, headers)
            if r.status_code == 304:
                result = FetchResult(source.id, url, "not_modified")
                state.consecutive_failures = 0
                state.last_ok_at = now
            else:
                r.raise_for_status()
                arts = parse_feed(source, r.content)
                state.etag = r.headers.get("ETag") or state.etag
                state.last_modified = r.headers.get("Last-Modified") or state.last_modified
                state.last_entries = len(arts)
                if arts:
                    state.consecutive_failures = 0
                    state.last_ok_at = now
                    state.last_error = None
                    state.open_until = None
                    result = FetchResult(source.id, url, "ok", articles=arts)
                else:
                    raise ValueError("feed valido ma vuoto")
        except Exception as e:
            state.consecutive_failures = (state.consecutive_failures or 0) + 1
            state.last_error = str(e)[:300]
            if state.consecutive_failures >= BREAKER_THRESHOLD:
                state.open_until = now + breaker_pause(state.consecutive_failures)
            result = FetchResult(source.id, url, "error", error=state.last_error)

        db.merge(state)
        db.commit()
    result.elapsed_ms = int((time.monotonic() - t0) * 1000)
    return result


def fetch_all(sources: List[SourceInfo], max_workers: int = 8) -> List[FetchResult]:
    jobs = [(s, u) for s in sources for u in s.feeds]
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(lambda j: fetch_one(*j), jobs))
