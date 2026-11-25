"""Arricchimento per-articolo (bias, embedding) e helper di clustering.

Il nome del modulo e' storico: ora passa da ``app.llm`` e funziona sia con
Anthropic che con OpenAI (o senza nessuno dei due).
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np
from sqlalchemy.orm import Session

from .. import llm
from ..db_orm import cache_analysis, get_cached_analysis
from ..sources import get_source, leaning_from_score

log = logging.getLogger("pulsar.enrich")

CONFIDENCE_THRESHOLD = 0.65


def is_ai_available() -> bool:
    return llm.available()


def get_embedding(text: str) -> Optional[List[float]]:
    return llm.embed(text)


def classify_bias(title: str, snippet: str, source_name: str, body: Optional[str] = None) -> dict:
    """Misura l'orientamento del *testo* (non della testata).

    Restituisce ``bias`` (fascia), ``score`` (-1..1), ``confidence`` e una
    spiegazione breve in italiano.
    """
    default = {"bias": "unknown", "score": None, "confidence": 0.0, "explanation": ""}
    if not llm.available():
        return default

    context = (body or snippet or "")[:2500]
    prompt = f"""Sei un analista dei media italiani. Valuta l'inquadramento politico di QUESTO testo, non la reputazione della testata.

Testata: {source_name}
Titolo: {title}
Testo: {context}

Regole:
- La cronaca puramente fattuale e' "center" con confidenza bassa (< 0.6).
- Alza la confidenza solo se ci sono aggettivi valutativi, scelta selettiva dei fatti, citazioni di una sola parte, o una tesi esplicita.
- "score" va da -1 (chiaramente progressista/sinistra) a +1 (chiaramente conservatore/destra).
- La spiegazione deve citare un elemento concreto del testo (una parola, una scelta, un'omissione). Max 25 parole, in italiano.

JSON: {{"bias": "left"|"center"|"right"|"unknown", "score": float, "confidence": float, "explanation": str}}"""
    try:
        data = llm.complete_json(prompt, tier="fast", max_tokens=300)
        score = data.get("score")
        score = max(-1.0, min(1.0, float(score))) if score is not None else None
        return {
            "bias": data.get("bias", "unknown") if data.get("bias") in ("left", "center", "right") else "unknown",
            "score": score,
            "confidence": float(data.get("confidence", 0.0) or 0.0),
            "explanation": (data.get("explanation") or "").strip(),
        }
    except Exception as e:
        log.warning("classify_bias fallita: %s", e)
        return default


def fuse_bias(article) -> None:
    """Layer di fusione: il testo vince sulla testata solo se l'AI e' sicura."""
    src = get_source(article.source_id)
    src_score = src.orientation if src else None
    if article.bias_confidence is not None and article.bias_confidence >= CONFIDENCE_THRESHOLD and article.bias_article not in (None, "unknown"):
        article.bias = article.bias_article
        if article.orientation_score is None:
            article.orientation_score = src_score
    else:
        article.bias = leaning_from_score(src_score) if src else (article.bias_source or "unknown")
        article.orientation_score = src_score


def enrich_article_smart(article, db: Session):
    """Bias + embedding con cache su DB. Modifica l'articolo in place."""
    cached = get_cached_analysis(db, article.url) if article.url else None
    if cached:
        article.bias_article = cached.get("bias_article")
        article.bias_confidence = cached.get("bias_confidence")
        article.bias_explanation = cached.get("bias_explanation")
        article.orientation_score = cached.get("orientation_score")
        article.embedding = cached.get("embedding")
        fuse_bias(article)
        return article

    if llm.available():
        res = classify_bias(article.title, article.snippet, article.source_name, article.body)
        article.bias_article = res["bias"]
        article.bias_confidence = res["confidence"]
        article.bias_explanation = res["explanation"]
        if res["score"] is not None and res["confidence"] >= CONFIDENCE_THRESHOLD:
            article.orientation_score = res["score"]
    fuse_bias(article)

    if llm.embeddings_available():
        body_part = (article.body or "")[:1000]
        article.embedding = llm.embed(f"{article.title} {article.snippet} {body_part}")

    if article.url and (article.bias_article or article.embedding):
        cache_analysis(
            db,
            article.url,
            article.bias,
            article.embedding,
            bias_article=article.bias_article,
            bias_confidence=article.bias_confidence,
            bias_explanation=article.bias_explanation,
            orientation_score=article.orientation_score,
        )
    return article


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2:
        return 0.0
    v1, v2 = np.array(vec1), np.array(vec2)
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))


def generate_story_title(titles: List[str]) -> str:
    if not llm.available() or not titles:
        return titles[0] if titles else "Nuova storia"
    listing = "\n".join(f"- {t}" for t in titles[:12])
    prompt = f"""Questi titoli parlano dello stesso fatto. Scrivi UN titolo in italiano, neutro e descrittivo:
- soggetto + verbo + fatto, niente aggettivi valutativi, niente virgolette, niente punti esclamativi;
- se i titoli sono in conflitto sui fatti, descrivi solo cio' su cui concordano;
- massimo 14 parole.

Titoli:
{listing}

Rispondi solo con il titolo."""
    try:
        return llm.complete_text(prompt, tier="fast", max_tokens=60).strip().strip('"').strip("«»")
    except Exception as e:
        log.warning("generate_story_title fallita: %s", e)
        return titles[0]


def check_clusters_merge(clusters_data: List[dict]) -> List[List[int]]:
    """Chiede al modello quali cluster descrivono lo stesso fatto."""
    if not llm.available() or len(clusters_data) < 2:
        return []
    listing = "\n".join(f"Cluster {c['id']}: " + " || ".join(c["titles"][:3]) for c in clusters_data)
    prompt = f"""Sei il caporedattore di un aggregatore di notizie. Ogni cluster e' rappresentato da alcuni titoli.
Indica i cluster che parlano dello STESSO fatto e vanno uniti.
- Unisci se e' lo stesso evento, o un suo sviluppo diretto nello stesso giorno.
- NON unire eventi distinti dello stesso tema (es. due manifestazioni in citta' diverse).

{listing}

JSON: {{"merges": [[id, id, ...], ...]}} (lista vuota se non serve unire)"""
    try:
        data = llm.complete_json(prompt, tier="fast", max_tokens=600)
        merges = data.get("merges", [])
        valid_ids = {c["id"] for c in clusters_data}
        return [[i for i in g if i in valid_ids] for g in merges if isinstance(g, list) and len(g) > 1]
    except Exception as e:
        log.warning("check_clusters_merge fallita: %s", e)
        return []
