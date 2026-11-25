"""Normalizzazione e deduplicazione degli articoli in ingresso.

Lo stesso articolo arriva spesso piu' volte: da due feed della stessa testata,
con parametri di tracciamento diversi, aggiornato con un titolo ritoccato.
Qui lo riconosciamo prima che entri nella pipeline.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Dict, Iterable, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..schemas import Article

TRACKING_PARAMS = re.compile(
    r"^(utm_|fbclid|gclid|ref|refresh_ce|ito|cmpid|xtor|ns_|mc_|amp$|output$|__twitter|ncid|ocid|sh$|rss$)", re.I
)


def canonical_url(url: str | None) -> str | None:
    """URL senza tracciamento, frammenti, 'www.' e slash finali; https sempre."""
    if not url:
        return None
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return url
    host = parts.netloc.lower().removeprefix("www.").removeprefix("m.")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False) if not TRACKING_PARAMS.match(k)]
    path = re.sub(r"/amp/?$", "", parts.path).rstrip("/") or "/"
    return urlunsplit(("https", host, path, urlencode(sorted(query)), ""))


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def title_key(source_id: str, title: str) -> str:
    """Chiave per riconoscere lo stesso pezzo con un titolo leggermente ritoccato."""
    toks = re.findall(r"[a-z0-9]+", _fold(title))
    toks = [t for t in toks if len(t) > 2][:10]
    return hashlib.md5(f"{source_id}|{' '.join(sorted(toks))}".encode()).hexdigest()


def stable_id(source_id: str, url: str | None, title: str) -> str:
    return hashlib.md5(f"{source_id}:{canonical_url(url) or title}".encode()).hexdigest()


def is_valid(a: Article) -> Tuple[bool, str]:
    title = (a.title or "").strip()
    if len(title) < 12:
        return False, "titolo troppo corto"
    if re.search(r"\b(oroscopo|meteo di oggi|lotto|superenalotto|estrazioni)\b", _fold(title)):
        return False, "rubrica di servizio"
    if a.url and re.search(r"/(video|foto|gallery|podcast)/", a.url) and not (a.snippet or a.body):
        return False, "contenuto multimediale senza testo"
    return True, ""


def normalize_and_dedupe(articles: Iterable[Article]) -> Tuple[List[Article], Dict[str, int]]:
    """Restituisce gli articoli unici e un conteggio dei motivi di scarto."""
    by_url: Dict[str, Article] = {}
    by_title: Dict[str, str] = {}
    dropped: Dict[str, int] = {}

    for a in articles:
        ok, why = is_valid(a)
        if not ok:
            dropped[why] = dropped.get(why, 0) + 1
            continue
        a.url = canonical_url(a.url)
        a.id = stable_id(a.source_id, a.url, a.title)
        key = a.url or a.id
        tkey = title_key(a.source_id, a.title)
        if key in by_url or tkey in by_title:
            dropped["duplicato"] = dropped.get("duplicato", 0) + 1
            existing = by_url.get(key) or by_url.get(by_title.get(tkey, ""))
            # tieni la versione piu' ricca
            if existing and len(a.body or a.snippet or "") > len(existing.body or existing.snippet or ""):
                existing.snippet, existing.body = a.snippet, a.body or existing.body
                existing.image_url = existing.image_url or a.image_url
            continue
        by_url[key] = a
        by_title[tkey] = key
    return list(by_url.values()), dropped
