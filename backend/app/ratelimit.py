"""Limite di richieste per IP, in memoria (sufficiente per un singolo processo).

Protegge le funzioni che costano (verifica, domande, voce) da abusi e da bot.
Dietro un proxy, l'IP viene letto da X-Forwarded-For.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_hits: dict = defaultdict(deque)
_lock = threading.Lock()


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "?"


def limit(request: Request, bucket: str, per_minute: int) -> None:
    key = (bucket, client_ip(request))
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= per_minute:
            retry = int(60 - (now - q[0])) + 1
            raise HTTPException(429, f"Troppe richieste: riprova tra {retry} secondi.", headers={"Retry-After": str(retry)})
        q.append(now)
