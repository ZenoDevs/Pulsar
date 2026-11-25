"""Argomenti: il catalogo, l'assegnazione alle storie e il feed personalizzato.

Niente account: il profilo del lettore vive nel suo browser e viene mandato a
/api/feed a ogni apertura. Il server non conserva nulla di personale.

Il profilo e' una lista di argomenti con un peso. Gli argomenti possono essere
del catalogo (con parole chiave curate) o liberi ("politica estera italiana",
"Formula 1"): per quelli liberi, se c'e' un modello, espandiamo le parole
chiave una volta e le mettiamo in cache.
"""

from __future__ import annotations

import logging
import math
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from . import llm

log = logging.getLogger("pulsar.topics")


@dataclass(frozen=True)
class Topic:
    id: str
    label: str
    keywords: List[str]
    sections: List[str] = field(default_factory=list)
    blurb: str = ""


CATALOG: List[Topic] = [
    Topic("esteri-italia", "Politica estera dell'Italia",
          ["farnesina", "ministro degli esteri", "esteri", "diplomazia", "ambasciat", "missione", "nato", "onu",
           "bilateral", "vertice", "accordo internazionale", "cooperazione internazionale", "parlamento approva la partecipazione"],
          ["Esteri"], "Diplomazia, missioni, alleanze, l'Italia nel mondo"),
    Topic("europa", "Europa e Ue",
          ["ue", "unione europea", "bruxelles", "commissione europea", "parlamento europeo", "eurozona", "bce", "strasburgo"],
          ["Esteri", "Economia"], "Bruxelles, regole comuni, voti europei"),
    Topic("politica", "Politica italiana",
          ["governo", "parlamento", "consiglio regionale", "maggioranza", "opposizione", "legge", "decreto", "voti favorevoli",
           "giunta", "ministro", "elezioni", "premier", "senato", "camera"],
          ["Politica"], "Governo, Parlamento, regioni, leggi"),
    Topic("economia", "Economia e conti",
          ["economia", "pil", "inflazione", "tasse", "manovra", "bilancio", "milioni di euro", "investiment", "round", "borsa", "imprese"],
          ["Economia"], "Conti pubblici, imprese, mercati"),
    Topic("lavoro", "Lavoro e diritti",
          ["lavoro", "lavorator", "sciopero", "sindacat", "contratto", "salari", "stipendi", "braccianti", "precari", "turni", "assunzion"],
          ["Economia", "Società"], "Contratti, salari, scioperi, condizioni di lavoro"),
    Topic("casa", "Casa e città",
          ["casa", "case", "affitt", "alloggi", "abitativ", "residenti", "centro storico", "urbanistic", "sindaco", "sindaca", "comune"],
          ["Società", "Politica"], "Affitti, quartieri, amministrazioni locali"),
    Topic("infrastrutture", "Infrastrutture e trasporti",
          ["ponte", "strada", "statale", "autostrad", "ferrovi", "stazion", "trasporto", "bus", "treni", "cantier", "manutenzione", "viabilit"],
          ["Cronaca", "Economia"], "Strade, ponti, treni, cantieri"),
    Topic("sicurezza", "Sicurezza e giustizia",
          ["procura", "indagine", "inchiesta", "furti", "reati", "denunc", "polizia", "carabinieri", "tribunale", "prefettura", "sentenza"],
          ["Cronaca"], "Indagini, processi, criminalità, dati sui reati"),
    Topic("clima-energia", "Clima ed energia",
          ["clima", "energia", "batterie", "rinnovabil", "emissioni", "gas", "elettric", "siccità", "alluvion", "ambiental"],
          ["Scienza", "Economia"], "Transizione, energia, eventi estremi"),
    Topic("tech", "Tecnologia e AI",
          ["intelligenza artificiale", "startup", "tecnologi", "digitale", "software", "cyber", "innovazion", "algoritm", "chip", "batterie"],
          ["Economia", "Scienza"], "AI, startup, digitale"),
    Topic("salute", "Salute",
          ["salute", "ospedal", "sanità", "medici", "pazienti", "vaccin", "malatti", "farmac"],
          ["Società"], "Sanità pubblica, ospedali, ricerca medica"),
    Topic("scuola", "Scuola e università",
          ["scuola", "studenti", "università", "insegnanti", "docenti", "maturità", "atenei", "istruzione"],
          ["Società"], "Istruzione, ricerca, giovani"),
    Topic("cultura", "Cultura",
          ["cultura", "museo", "mostra", "libro", "cinema", "teatro", "musica", "festival", "soprintendenza"],
          ["Cultura"], "Arte, libri, cinema, musica"),
    Topic("sport", "Sport",
          ["calcio", "serie a", "campionato", "partita", "olimpi", "tennis", "formula 1", "motogp", "allenatore"],
          ["Sport"], "Calcio, tennis, motori e il resto"),
]

TOPICS: Dict[str, Topic] = {t.id: t for t in CATALOG}
_EXPANDED: Dict[str, List[str]] = {}


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def _kw_hits(text: str, keywords: List[str]) -> int:
    """Quante parole chiave distinte compaiono. Le chiavi brevi richiedono la
    parola intera, le altre valgono anche come prefisso (affitt -> affitti)."""
    hits = 0
    for kw in keywords:
        k = fold(kw).strip()
        if not k:
            continue
        pattern = rf"\b{re.escape(k)}\b" if len(k) <= 3 else rf"\b{re.escape(k)}"
        if re.search(pattern, text):
            hits += 1
    return hits


def expand_custom(label: str) -> List[str]:
    """Parole chiave per un argomento libero. Con il modello: 10-15 termini
    italiani; senza: le parole del nome stesso, troncate a radice."""
    key = fold(label).strip()
    if key in _EXPANDED:
        return _EXPANDED[key]
    base = [w[:-1] if len(w) > 5 else w for w in re.findall(r"[a-z0-9]+", key) if len(w) > 2]
    words = list(dict.fromkeys([key] + base))
    if llm.available():
        try:
            data = llm.complete_json(
                f"""Un lettore italiano vuole seguire l'argomento: "{label}".
Elenca 12 parole o brevi espressioni (in italiano, minuscolo) che compaiono tipicamente nei titoli e nei testi
degli articoli su questo argomento: nomi di istituzioni, luoghi, persone ricorrenti, termini tecnici.
JSON: {{"parole": ["..."]}}""",
                tier="fast",
                max_tokens=300,
                required_keys=("parole",),
            )
            words += [w for w in data.get("parole", []) if isinstance(w, str)]
        except Exception as e:
            log.warning("Espansione argomento fallita: %s", e)
    _EXPANDED[key] = list(dict.fromkeys(w.strip() for w in words if w.strip()))[:20]
    return _EXPANDED[key]


def story_text(story) -> str:
    parts = [story.title or ""]
    for a in story.articles[:12]:
        parts += [a.title, a.snippet or ""]
    d = story.dossier
    if d:
        parts += [d.summary or ""] + [f.text for f in d.facts]
    return fold(" ".join(parts))


def match_score(text: str, section: Optional[str], keywords: List[str], sections: List[str]) -> float:
    hits = _kw_hits(text, keywords)
    score = 1 - math.exp(-0.6 * hits)  # 1 hit ~0.45, 3 hit ~0.83
    if section and section in sections:
        score = min(1.0, score + 0.25)
    return round(score, 3)


def assign_topics(story) -> List[str]:
    text = story_text(story)
    scored = [(t.id, match_score(text, story.section, t.keywords, t.sections)) for t in CATALOG]
    return [tid for tid, s in sorted(scored, key=lambda x: -x[1]) if s >= 0.6][:3]


# --------------------------------------------------------------------------
# Feed personalizzato
# --------------------------------------------------------------------------


def _freshness(last: Optional[datetime], now: datetime) -> float:
    if last is None:
        return 0.5
    if last.tzinfo:
        last = last.replace(tzinfo=None)
    hours = max(0.0, (now - last).total_seconds() / 3600)
    return 0.5 ** (hours / 24)


def personalize(summaries, profile: dict) -> dict:
    """Ordina le storie per il lettore.

    profile = {
      "topics": [{"id": "esteri-italia", "weight": 1.0} | {"label": "Formula 1", "weight": 0.8}],
      "seen": ["story-id", ...],          # gia' lette oggi: scendono
      "more": ["story-id"], "less": ["story-id"],  # segnali espliciti
      "sections": {"Esteri": 0.4, ...}    # affinita' apprese dal comportamento
    }
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    topics = []
    for t in profile.get("topics") or []:
        w = float(t.get("weight", 1.0) or 1.0)
        if t.get("id") in TOPICS:
            cat = TOPICS[t["id"]]
            topics.append((cat.id, cat.label, cat.keywords, cat.sections, w))
        elif t.get("label"):
            label = t["label"].strip()[:60]
            topics.append((f"custom:{fold(label)}", label, expand_custom(label), [], w))

    seen = set(profile.get("seen") or [])
    less = set(profile.get("less") or [])
    section_aff = profile.get("sections") or {}
    max_score = max((s.score for s in summaries), default=1.0) or 1.0

    rails: Dict[str, dict] = {tid: {"id": tid, "label": label, "stories": []} for tid, label, *_ in topics}
    ranked = []
    for s in summaries:
        text = fold(" ".join([s.title, s.summary or ""] + [h.title for h in s.headlines] + [f.text for f in s.key_facts]))
        best, best_label, total = 0.0, None, 0.0
        for tid, label, kws, secs, w in topics:
            m = match_score(text, s.section, kws, secs)
            if m >= 0.45:
                rails[tid]["stories"].append((m, s))
            total += m * w
            if m * w > best:
                best, best_label = m * w, label
        importance = s.score / max_score
        affinity = float(section_aff.get(s.section or "", 0.0))
        rank = 0.45 * min(1.0, total) + 0.35 * importance + 0.1 * _freshness(s.stats.last_published_at, now) + 0.1 * affinity
        if s.id in seen:
            rank *= 0.35
        if s.id in less:
            rank *= 0.2
        reason = f"Perché segui {best_label}" if best_label and best >= 0.45 else ("Tra le più importanti di oggi" if importance > 0.6 else None)
        ranked.append((rank, s.model_copy(update={"reason": reason})))

    ranked.sort(key=lambda x: -x[0])
    out_rails = []
    for r in rails.values():
        stories = [s.model_copy(update={"reason": f"Perché segui {r['label']}"}) for _, s in sorted(r["stories"], key=lambda x: -x[0])]
        out_rails.append({"id": r["id"], "label": r["label"], "stories": stories})
    return {"for_you": [s for _, s in ranked], "rails": out_rails}
