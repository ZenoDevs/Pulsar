"""Quante voci indipendenti raccontano davvero questa storia?

Dieci articoli non sono dieci conferme se:
- sono di testate dello stesso editore (stesso ``owner_group``);
- sono riprese quasi letterali dello stesso lancio d'agenzia.

Qui misuriamo entrambe le cose in modo deterministico, senza AI: le regole
devono essere verificabili da chiunque.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set, Tuple

from ..schemas import Article
from ..sources import is_agency, owner_group_of

SHINGLE_SIZE = 5
ECHO_THRESHOLD = 0.45  # quota di 5-grammi condivisi oltre la quale e' una ripresa


def _normalize(text: str) -> List[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", text)


def shingles(text: str, k: int = SHINGLE_SIZE) -> Set[Tuple[str, ...]]:
    toks = _normalize(text)
    if len(toks) < k:
        return {tuple(toks)} if toks else set()
    return {tuple(toks[i : i + k]) for i in range(len(toks) - k + 1)}


def containment(a: Set, b: Set) -> float:
    """Quanta parte di ``a`` e' contenuta in ``b`` (asimmetrica: un pezzo
    breve che riprende un lancio lungo risulta comunque una ripresa)."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a)


def _text_of(a: Article) -> str:
    return f"{a.snippet or ''} {(a.body or '')[:2500]}".strip()


def _ts(a: Article) -> datetime:
    return a.published_at or datetime.max


def detect_echoes(articles: List[Article], threshold: float = ECHO_THRESHOLD) -> None:
    """Marca ``echo_of`` sugli articoli che riprendono un testo precedente.

    L'originale e' il primo pubblicato (le agenzie vincono a parita' di ora).
    Modifica gli articoli in place.
    """
    ordered = sorted(articles, key=lambda a: (_ts(a), 0 if is_agency(a.source_id) else 1))
    sh: Dict[str, Set] = {a.id: shingles(_text_of(a)) for a in ordered}
    for i, a in enumerate(ordered):
        a.echo_of, a.echo_similarity = None, None
        if len(sh[a.id]) < 8:  # testo troppo corto per giudicare
            continue
        best: Optional[Tuple[float, Article]] = None
        for prev in ordered[:i]:
            if prev.source_id == a.source_id:
                continue
            c = containment(sh[a.id], sh[prev.id])
            if c >= threshold and (best is None or c > best[0]):
                best = (c, prev)
        if best:
            a.echo_of = best[1].echo_of or best[1].id  # risali all'originale
            a.echo_similarity = round(best[0], 2)


def independent_voices(articles: Iterable[Article], universe: Optional[Dict[str, Article]] = None) -> int:
    """Numero di gruppi editoriali distinti che hanno scritto un testo proprio.

    Le riprese di agenzia contano per la *fonte originale*, non per chi
    le ripubblica.
    """
    by_id = {a.id: a for a in articles}
    lookup = {**(universe or {}), **by_id}
    groups: Set[str] = set()
    for a in by_id.values():
        if a.echo_of and a.echo_of in lookup:
            groups.add(owner_group_of(lookup[a.echo_of].source_id))
        elif a.echo_of:
            # l'originale non e' tra gli articoli citati: e' comunque una voce
            # non indipendente, la contiamo come quella dell'originale sconosciuto
            groups.add(f"echo:{a.echo_of}")
        else:
            groups.add(owner_group_of(a.source_id))
    return len(groups)


def independence_summary(articles: List[Article]) -> dict:
    return {
        "articles": len(articles),
        "outlets": len({a.source_id for a in articles}),
        "owner_groups": len({owner_group_of(a.source_id) for a in articles}),
        "echoes": sum(1 for a in articles if a.echo_of),
        "independent_voices": independent_voices(articles),
    }
