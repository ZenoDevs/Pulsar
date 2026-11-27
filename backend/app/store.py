"""Accesso alle storie correnti (edizione reale o demo), con cache in memoria."""

from __future__ import annotations

import time
from datetime import datetime
from typing import List

from .pipeline import STORY_CACHE
from .schemas import Story

_CACHE = {"at": 0.0, "stories": []}
TTL_SECONDS = 60


def current_stories(demo: bool) -> List[Story]:
    if demo:
        from .demo import build_demo_edition

        if not any(k.startswith("demo-") for k in STORY_CACHE):
            build_demo_edition()
        return [s for k, s in STORY_CACHE.items() if k.startswith("demo-")]

    if time.monotonic() - _CACHE["at"] < TTL_SECONDS and _CACHE["stories"]:
        return _CACHE["stories"]
    from .aggregator.worker import load_open_stories

    stories = load_open_stories(datetime.utcnow())
    _CACHE.update(at=time.monotonic(), stories=stories)
    for s in stories:
        STORY_CACHE[s.id] = s
    return stories
