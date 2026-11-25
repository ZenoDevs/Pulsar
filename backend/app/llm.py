"""Astrazione minima sui modelli linguistici.

Pulsar funziona con:
- Anthropic (``ANTHROPIC_API_KEY``) — consigliato per il dossier, dove serve
  ragionamento attento su fonti in conflitto;
- OpenAI (``OPENAI_API_KEY``) — supportato come prima, e unico provider per
  gli embedding;
- nessuna chiave — Pulsar resta utilizzabile: clustering TF-IDF, bias dalla
  fonte, metriche deterministiche. Mancano solo i dossier generati.

Variabili d'ambiente:
- ``PULSAR_LLM_PROVIDER``: ``anthropic`` | ``openai`` (default: il primo con chiave)
- ``PULSAR_MODEL_DEEP``: modello per il dossier
- ``PULSAR_MODEL_FAST``: modello per classificazioni per-articolo
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("pulsar.llm")

_ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
_OPENAI_KEY = os.getenv("OPENAI_API_KEY")

_anthropic = None
_openai = None

if _ANTHROPIC_KEY:
    try:
        import anthropic

        _anthropic = anthropic.Anthropic(api_key=_ANTHROPIC_KEY)
    except Exception as e:  # pragma: no cover
        log.warning("Anthropic non disponibile: %s", e)

if _OPENAI_KEY:
    try:
        from openai import OpenAI

        _openai = OpenAI(api_key=_OPENAI_KEY)
    except Exception as e:  # pragma: no cover
        log.warning("OpenAI non disponibile: %s", e)


def provider() -> Optional[str]:
    forced = os.getenv("PULSAR_LLM_PROVIDER")
    if forced == "anthropic" and _anthropic:
        return "anthropic"
    if forced == "openai" and _openai:
        return "openai"
    if _anthropic:
        return "anthropic"
    if _openai:
        return "openai"
    return None


def available() -> bool:
    return provider() is not None


def embeddings_available() -> bool:
    return _openai is not None


_DEFAULTS = {
    "anthropic": {"deep": "claude-sonnet-5-5", "fast": "claude-haiku-5-5"},
    "openai": {"deep": "gpt-4o", "fast": "gpt-4o-mini"},
}


def _model(tier: str) -> str:
    p = provider() or "openai"
    env = os.getenv("PULSAR_MODEL_DEEP" if tier == "deep" else "PULSAR_MODEL_FAST")
    return env or _DEFAULTS[p][tier]


def extract_json(text: str) -> dict:
    """Estrae il primo oggetto JSON da una risposta (tollera ```json ... ```)."""
    if not text:
        raise ValueError("risposta vuota")
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        text = fenced.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("nessun JSON nella risposta")
    return json.loads(text[start : end + 1])


def complete_json(
    prompt: str,
    *,
    system: str = "Rispondi solo con un oggetto JSON valido.",
    tier: str = "fast",
    max_tokens: int = 1500,
    temperature: float = 0.0,
) -> dict:
    """Chiede al modello un JSON e lo restituisce gia' parsato."""
    p = provider()
    if p is None:
        raise RuntimeError("Nessun provider LLM configurato")

    if p == "anthropic":
        resp = _anthropic.messages.create(
            model=_model(tier),
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return extract_json(text)

    resp = _openai.chat.completions.create(
        model=_model(tier),
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return extract_json(resp.choices[0].message.content)


def complete_text(prompt: str, *, tier: str = "fast", max_tokens: int = 200, temperature: float = 0.3) -> str:
    p = provider()
    if p is None:
        raise RuntimeError("Nessun provider LLM configurato")
    if p == "anthropic":
        resp = _anthropic.messages.create(
            model=_model(tier),
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    resp = _openai.chat.completions.create(
        model=_model(tier),
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def embed(text: str) -> Optional[List[float]]:
    if not _openai:
        return None
    try:
        r = _openai.embeddings.create(input=[text.replace("\n", " ")[:8000]], model="text-embedding-3-small")
        return r.data[0].embedding
    except Exception as e:
        log.warning("Errore embedding: %s", e)
        return None
