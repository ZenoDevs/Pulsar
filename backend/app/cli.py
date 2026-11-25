"""Comandi da terminale.

    python -m app.cli check-feeds     # verifica che i feed RSS rispondano
    python -m app.cli edition         # genera una nuova prima pagina
"""

from __future__ import annotations

import sys

from .ingest.rss import fetch_feed
from .sources import real_sources


def check_feeds() -> int:
    bad = 0
    for s in real_sources():
        for url in s.feeds:
            arts, h = fetch_feed(s, url)
            mark = "OK " if h.ok else "ERR"
            bad += 0 if h.ok else 1
            print(f"[{mark}] {s.name:<22} {h.entries:>3} articoli  {url}" + (f"  ({h.error})" if h.error else ""))
    print(f"\n{bad} feed da correggere in app/sources.py" if bad else "\nTutti i feed rispondono.")
    return 1 if bad else 0


def edition() -> int:
    from .edition import build_edition

    e = build_edition(progress=print)
    if not e:
        print("Nessuna edizione generata (nessun articolo dai feed).")
        return 1
    print(f"Edizione {e.id}: {len(e.stories)} storie, {e.articles_analyzed} articoli, {e.sources_ok}/{e.sources_total} fonti")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit({"check-feeds": check_feeds, "edition": edition}.get(cmd, lambda: print(__doc__) or 2)())
