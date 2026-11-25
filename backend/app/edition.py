"""La prima pagina. La logica vive nell'aggregatore (app/aggregator/worker.py)."""

from __future__ import annotations

from typing import Callable, Optional

from .aggregator.worker import run_once
from .schemas import Edition


def build_edition(progress: Callable[[str], None] = lambda _: None, **_) -> Optional[Edition]:
    return run_once(progress=progress)
