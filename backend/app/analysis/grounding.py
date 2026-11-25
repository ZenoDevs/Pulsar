"""Ancoraggio: ogni fatto deve poggiare su parole che esistono davvero.

Il modello, per ogni fatto, deve copiare una breve citazione dall'articolo che
cita. Qui verifichiamo che quella citazione si ritrovi nel testo (con
tolleranza per punteggiatura, accenti e piccole differenze). Una citazione che
non si trova e' il segnale piu' affidabile di un'allucinazione: la fonte
relativa viene tolta dal fatto, e un fatto senza piu' citazioni valide diventa
"non verificato".
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Tuple

from ..schemas import Article

NGRAM = 3
MATCH_THRESHOLD = 0.75  # quota di trigrammi della citazione presenti nel testo


def _tokens(text: str) -> List[str]:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", text)


def quote_match(quote: str, article: Article) -> float:
    """Quota (0-1) dei trigrammi della citazione che compaiono nel testo dell'articolo."""
    q = _tokens(quote)
    if len(q) < 3:
        return 0.0
    hay = _tokens(f"{article.title} {article.snippet} {article.body or ''}")
    if not hay:
        return 0.0
    grams = {tuple(hay[i : i + NGRAM]) for i in range(len(hay) - NGRAM + 1)}
    qg = [tuple(q[i : i + NGRAM]) for i in range(len(q) - NGRAM + 1)]
    return sum(1 for g in qg if g in grams) / len(qg)


def verify(quote: str, article: Article) -> Tuple[bool, float]:
    m = round(quote_match(quote, article), 2)
    return m >= MATCH_THRESHOLD, m
