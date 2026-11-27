"""Verifica di un'affermazione e domande su una storia.

Due funzioni che portano la verifica fuori da Pulsar:

``check_claim``: incolli una frase vista altrove ("hanno arrestato il sindaco",
"tre morti nel crollo") e Pulsar la confronta con i fatti, le interpretazioni
e i titoli di tutte le storie correnti. Il verdetto ha lo stesso vocabolario
del dossier, piu' due stati: "opinione" (corrisponde a un'interpretazione, non
a un fatto) e "non trovata" (nessuna testata la riporta: non vuol dire falsa).

``ask_story``: una domanda su una storia. Senza modello la risposta e'
estrattiva (le frasi piu' pertinenti degli articoli, con la fonte). Con il
modello la risposta e' generata, ma deve citare frasi letterali che vengono
verificate nel testo; se nessuna citazione regge, si torna all'estrattiva.

Entrambe funzionano senza chiavi API: la base e' la similarita' testuale
(TF-IDF su n-grammi di caratteri, robusta alle flessioni dell'italiano).
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer

from .. import llm
from ..schemas import Article, Story
from ..sources import get_source
from .grounding import verify

log = logging.getLogger("pulsar.qa")

# --------------------------------------------------------------------------
# Strumenti comuni
# --------------------------------------------------------------------------

NUM_WORDS = {
    "un": 1, "uno": 1, "una": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6, "sette": 7,
    "otto": 8, "nove": 9, "dieci": 10, "undici": 11, "dodici": 12, "venti": 20, "trenta": 30,
    "cento": 100, "mille": 1000,
}


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def numbers_in(text: str) -> set:
    """Numeri in cifre o in lettere (le parole numero ambigue come 'una' contano
    solo se seguite da un sostantivo plausibile: persona, ferito, morto, ...)."""
    t = fold(text)
    out = set()
    for m in re.finditer(r"\d+(?:[.,]\d+)?", t):
        raw = m.group().replace(".", "").replace(",", ".")
        try:
            v = float(raw)
            out.add(int(v) if v.is_integer() else v)
        except ValueError:
            pass
    for w, v in NUM_WORDS.items():
        if v == 1:
            if re.search(rf"\b{w}\s+(persona|ferit|mort|vittim|arrest|feriti)", t):
                out.add(1)
        elif re.search(rf"\b{w}\b", t):
            out.add(v)
    return out


def _vectorizer():
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, strip_accents="unicode", lowercase=True)


def similarities(query: str, texts: List[str]) -> np.ndarray:
    if not texts:
        return np.array([])
    vec = _vectorizer()
    clean = lambda t: re.sub(r"[’'`]", " ", t)  # l'Italia == l Italia == all'Italia
    X = vec.fit_transform([clean(t) for t in texts] + [clean(query)])
    M = X[:-1]
    q = X[-1]
    return (M @ q.T).toarray().ravel()


def names_of(ids: List[str]) -> List[str]:
    return [get_source(i).name if get_source(i) else i for i in ids]


# --------------------------------------------------------------------------
# Verifica di un'affermazione
# --------------------------------------------------------------------------


class CheckMatch(BaseModel):
    kind: str  # fatto | interpretazione | versione | titolo
    text: str
    status: Optional[str] = None
    source_ids: List[str] = []
    source_names: List[str] = []
    similarity: float
    story_id: str
    story_title: str


class CheckResult(BaseModel):
    claim: str
    verdict: str  # confermato | riportato | contestato | non_verificato | opinione | contraddetto | se_ne_parla | non_trovata
    headline: str
    explanation: str
    story_id: Optional[str] = None
    story_title: Optional[str] = None
    matches: List[CheckMatch] = []
    claim_numbers: List[float] = []
    source_numbers: List[float] = []
    numbers_mismatch: bool = False
    method: str = "confronto testuale"
    stories_searched: int = 0


@dataclass
class _Unit:
    kind: str
    text: str
    story: Story
    status: Optional[str] = None
    source_ids: List[str] = field(default_factory=list)
    extra: str = ""

    @property
    def match_text(self) -> str:
        return f"{self.text} {self.extra}".strip()


def _units(stories: List[Story]) -> List[_Unit]:
    units: List[_Unit] = []
    for s in stories:
        d = s.dossier
        if d:
            for f in d.facts:
                extra = " ".join([f.note or ""] + [e.quote for e in f.evidence if e.verified])
                units.append(_Unit("fatto", f.text, s, f.status, f.source_ids, extra))
            for it in d.interpretations:
                units.append(_Unit("interpretazione", it.text, s, None, it.source_ids))
            for dv in d.divergences:
                for v in dv.versions:
                    units.append(_Unit("versione", f"{dv.topic}: {v.account}", s, "contestato", v.source_ids))
        for a in s.articles:
            units.append(_Unit("titolo", a.title, s, None, [a.source_id]))
    return units


T_STRONG = 0.42  # corrispondenza diretta
T_WEAK = 0.24  # se ne parla


HEADLINES = {
    "confermato": "Confermato da più voci indipendenti",
    "riportato": "Riportato, ma da una sola fonte",
    "contestato": "Le testate non concordano",
    "non_verificato": "Circola, ma nessuno lo ha verificato",
    "opinione": "È un'opinione, non un fatto",
    "contraddetto": "Le testate dicono un'altra cosa",
    "se_ne_parla": "Se ne parla, ma non in questi termini",
    "non_trovata": "Nessuna testata lo riporta",
}


def check_claim(claim: str, stories: List[Story]) -> CheckResult:
    claim = re.sub(r"\s+", " ", claim or "").strip()[:500]
    base = CheckResult(claim=claim, verdict="non_trovata", headline=HEADLINES["non_trovata"], explanation="", stories_searched=len(stories))
    units = _units(stories)
    if not claim or not units:
        base.explanation = "Non ci sono storie su cui verificare in questo momento."
        return base

    sims = similarities(claim, [u.match_text for u in units])
    order = np.argsort(-sims)

    # storia di riferimento: quella con la somma delle tre migliori corrispondenze
    by_story: Dict[str, List[float]] = {}
    for i in order[:60]:
        by_story.setdefault(units[i].story.id, []).append(float(sims[i]))
    best_story_id = max(by_story, key=lambda k: sum(sorted(by_story[k], reverse=True)[:3]))
    story = next(s for s in stories if s.id == best_story_id)

    top = [i for i in order if units[i].story.id == best_story_id][:6]
    matches = [
        CheckMatch(
            kind=units[i].kind, text=units[i].text, status=units[i].status,
            source_ids=units[i].source_ids, source_names=names_of(units[i].source_ids),
            similarity=round(float(sims[i]), 3), story_id=story.id, story_title=story.title,
        )
        for i in top
        if sims[i] >= T_WEAK * 0.8
    ]
    best_fact = next((m for m in matches if m.kind == "fatto"), None)
    best_interp = next((m for m in matches if m.kind == "interpretazione"), None)
    best_any = matches[0] if matches else None

    result = base.model_copy(update={"story_id": story.id, "story_title": story.title, "matches": matches})
    if not best_any or best_any.similarity < T_WEAK:
        result.story_id = result.story_title = None
        result.matches = []
        result.explanation = (
            f"Abbiamo cercato tra {len(stories)} storie di oggi e nessuna testata riporta questa notizia. "
            "Non significa che sia falsa: può essere troppo recente, locale, o non vera. Diffida di chi non cita una fonte."
        )
        return _numbers(result, claim, story)

    # Interpretazione che somiglia piu' di qualunque fatto
    if best_interp and best_interp.similarity >= T_STRONG and (not best_fact or best_interp.similarity > best_fact.similarity + 0.05):
        who = ", ".join(best_interp.source_names) or "alcune testate"
        result.verdict = "opinione"
        result.explanation = f"Corrisponde a una lettura dei fatti sostenuta da {who}, non a un fatto accertato. Altre testate la raccontano diversamente."
    elif best_fact and (best_fact.similarity >= T_STRONG or (best_fact.similarity >= 0.33 and best_fact.similarity >= best_any.similarity - 0.06)):
        result.verdict = best_fact.status or "non_verificato"
        who = ", ".join(best_fact.source_names)
        explain = {
            "confermato": f"Lo riportano in modo concorde voci indipendenti: {who}.",
            "riportato": f"Lo riporta {who}, ma non ci sono conferme indipendenti. Potrebbe cambiare.",
            "contestato": "Le testate danno versioni incompatibili su questo punto.",
            "non_verificato": f"Lo scrive {who} citando fonti anonime o indiscrezioni. Nessuno lo ha verificato.",
        }
        result.explanation = explain.get(result.verdict, "")
        if result.verdict == "contestato":
            versions = [m for m in matches if m.kind == "versione"]
            if versions:
                result.explanation += " " + " ".join(f"Per {', '.join(v.source_names)}: {_lc(v.text.split(': ', 1)[-1])}" for v in versions[:2])
    else:
        result.verdict = "se_ne_parla"
        result.explanation = f"La storia è questa: «{story.title}». Ma nessun fatto accertato corrisponde esattamente a quello che hai scritto."

    # L'affermazione tocca un punto su cui le testate si dividono?
    div = _touched_divergence(claim, story)
    if div is not None and result.verdict == "non_verificato":
        result.explanation += f" E su questo punto le testate si dividono: " + " ".join(
            f"per {', '.join(names_of(v.source_ids))}, {v.account[0].lower() + v.account[1:]}" for v in div.versions[:2]
        )
    elif div is not None and result.verdict in ("se_ne_parla", "riportato"):
        result.verdict = "contestato"
        result.explanation = f"Su questo punto ({div.topic.lower()}) le testate non concordano. " + " ".join(
            f"Per {', '.join(names_of(v.source_ids))}: {v.account[0].lower() + v.account[1:]}" for v in div.versions[:3]
        )
        return _finish(result, claim, story, skip_numbers=True)

    return _finish(result, claim, story)


def _touched_divergence(claim: str, story: Story):
    d = story.dossier
    if not d or not d.divergences:
        return None
    cn = numbers_in(claim)
    best, best_sim = None, 0.0
    for dv in d.divergences:
        texts = [dv.topic] + [v.account for v in dv.versions]
        sim = float(similarities(claim, [" ".join(texts)])[0])
        nums = set()
        for t in texts:
            nums |= numbers_in(t)
        if cn & nums:
            sim += 0.15
        if sim > best_sim:
            best, best_sim = dv, sim
    return best if best_sim >= 0.22 else None


def _finish(result: CheckResult, claim: str, story: Story, skip_numbers: bool = False) -> CheckResult:
    if not skip_numbers:
        result = _numbers(result, claim, story)
    else:
        result.claim_numbers = sorted(numbers_in(claim))
    if result.numbers_mismatch and result.verdict in ("confermato", "riportato", "se_ne_parla"):
        was_vague = result.verdict == "se_ne_parla"
        result.verdict = "contraddetto"
        numbers = (
            f"I numeri non tornano: tu scrivi {', '.join(_fmt(n) for n in result.claim_numbers)}, "
            f"le testate riportano {', '.join(_fmt(n) for n in result.source_numbers[:6])}."
        )
        result.explanation = numbers + (f" La notizia è questa: «{story.title}»." if was_vague else " " + result.explanation)

    if llm.available():
        result = _llm_refine(result, claim)
    result.headline = HEADLINES.get(result.verdict, result.headline)
    return result


def _lc(t: str) -> str:
    return t[:1].lower() + t[1:] if t else t


def _fmt(n) -> str:
    return str(int(n)) if float(n).is_integer() else str(n).replace(".", ",")


def _numbers(result: CheckResult, claim: str, story: Story) -> CheckResult:
    cn = numbers_in(claim)
    if not cn or not result.story_id:
        result.claim_numbers = sorted(cn)
        return result
    texts = [m.text for m in result.matches if m.kind in ("fatto", "versione", "titolo")]
    # anche i fatti della storia vicini all'affermazione, detti con altre parole
    if story.dossier and story.dossier.facts:
        fs = similarities(claim, [f.text for f in story.dossier.facts])
        texts += [f.text for f, v in zip(story.dossier.facts, fs) if v >= 0.15]
    sn = set()
    for t in texts:
        sn |= numbers_in(t)
    result.claim_numbers = sorted(cn)
    result.source_numbers = sorted(sn)
    # mismatch solo se le testate citano numeri e nessuno coincide
    result.numbers_mismatch = bool(sn) and not (cn & sn)
    return result


def _llm_refine(result: CheckResult, claim: str) -> CheckResult:
    if not result.matches:
        return result
    listing = "\n".join(f"[{i + 1}] ({m.kind}{', ' + m.status if m.status else ''}) {m.text} — {', '.join(m.source_names)}" for i, m in enumerate(result.matches))
    try:
        data = llm.complete_json(
            f"""Affermazione da verificare: "{claim}"

Elementi estratti dalle testate (gia' verificati da Pulsar):
{listing}

L'affermazione e' sostenuta, contraddetta o solo parzialmente toccata da questi elementi?
Usa SOLO questi elementi. JSON: {{"relazione": "sostiene|contraddice|parziale|non_correlata", "elementi": [n, ...], "spiegazione": "max 35 parole, italiano piano"}}""",
            tier="fast",
            max_tokens=300,
            required_keys=("relazione",),
        )
    except Exception as e:
        log.warning("Raffinamento LLM fallito: %s", e)
        return result
    rel = data.get("relazione")
    expl = (data.get("spiegazione") or "").strip()
    if rel == "contraddice":
        result.verdict = "contraddetto"
    elif rel == "non_correlata" and result.verdict not in ("non_trovata",):
        result.verdict = "se_ne_parla"
    elif rel == "parziale" and result.verdict == "confermato":
        result.verdict = "riportato"
    if expl:
        result.explanation = expl + (" " + result.explanation if result.numbers_mismatch else "")
    result.method = "confronto testuale + modello"
    return result


# --------------------------------------------------------------------------
# Domande su una storia
# --------------------------------------------------------------------------


class AnswerCitation(BaseModel):
    text: str
    source_id: str
    source_name: str
    article_id: str
    verified: bool = True
    also_in: List[str] = []
    fact_status: Optional[str] = None


class AnswerResult(BaseModel):
    question: str
    answer: Optional[str] = None
    certainty: Optional[str] = None  # confermato | riportato | contestato | non_si_sa
    citations: List[AnswerCitation] = []
    method: str = "estrattivo"
    note: Optional[str] = None


QUESTION_WORDS = {
    "chi", "che", "cosa", "come", "quando", "dove", "perche", "quanti", "quante", "quanto", "quale", "quali",
    "ci", "sono", "stati", "state", "stato", "e", "ha", "hanno", "il", "lo", "la", "i", "gli", "le", "di", "a",
    "da", "in", "su", "per", "un", "una", "del", "della", "dei", "si", "sa", "sai", "dimmi", "mi",
}


def _core(question: str) -> str:
    """La domanda senza le parole interrogative: resta il contenuto da cercare."""
    toks = re.findall(r"[a-z0-9]+", fold(question))
    core = [t for t in toks if t not in QUESTION_WORDS]
    return " ".join(core) or question


def _sentences(a: Article) -> List[str]:
    text = f"{a.body or a.snippet or ''}"
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if 30 <= len(p.strip()) <= 400]


def ask_story(story: Story, question: str) -> AnswerResult:
    question = re.sub(r"\s+", " ", question or "").strip()[:300]
    res = AnswerResult(question=question)
    if not question:
        return res

    # frasi uniche: una frase ripresa da piu' testate conta una volta, con "anche in"
    seen: Dict[str, AnswerCitation] = {}
    pool: List[AnswerCitation] = []
    for a in sorted(story.articles, key=lambda a: (bool(a.echo_of), a.published_at is None)):
        for sent in _sentences(a):
            key = re.sub(r"[^a-z0-9]", "", fold(sent))[:120]
            if key in seen:
                if a.source_name not in seen[key].also_in and a.source_name != seen[key].source_name:
                    seen[key].also_in.append(a.source_name)
                continue
            c = AnswerCitation(text=sent, source_id=a.source_id, source_name=a.source_name, article_id=a.id)
            seen[key] = c
            pool.append(c)
    if not pool:
        res.note = "Gli articoli di questa storia non hanno abbastanza testo per rispondere."
        return res

    sims = similarities(_core(question), [c.text for c in pool])
    order = [i for i in np.argsort(-sims) if sims[i] >= 0.08]
    facts = story.dossier.facts if story.dossier else []
    if facts and order:
        ftexts = [" ".join([f.text] + [e.quote for e in f.evidence if e.verified]) for f in facts]
        fsims = {i: similarities(pool[i].text, ftexts) for i in order[:8]}
        for i, fs in fsims.items():
            j = int(np.argmax(fs))
            if fs[j] >= 0.35:
                pool[i].fact_status = facts[j].status

    extractive = [pool[i] for i in order[:5]]
    if llm.available() and order:
        generated = _llm_answer(story, question, [pool[i] for i in order[:20]])
        if generated:
            return generated
        res.note = "La risposta generata non era ancorata ai testi: ti mostriamo le frasi pertinenti."

    res.citations = extractive
    if not extractive:
        res.note = "Gli articoli non contengono una risposta a questa domanda. Forse non si sa ancora: guarda «Cosa non sappiamo ancora»."
        res.certainty = "non_si_sa"
    else:
        statuses = [c.fact_status for c in extractive if c.fact_status]
        res.certainty = "contestato" if "contestato" in statuses else (statuses[0] if statuses else None)
    return res


def _llm_answer(story: Story, question: str, candidates: List[AnswerCitation]) -> Optional[AnswerResult]:
    by_id = {a.id: a for a in story.articles}
    listing = "\n".join(f"[{i + 1}] {c.source_name}: {c.text}" for i, c in enumerate(candidates))
    try:
        data = llm.complete_json(
            f"""Domanda di un lettore sulla notizia «{story.title}»: "{question}"

Frasi dagli articoli:
{listing}

Rispondi SOLO con quello che dicono queste frasi. Se le testate non concordano, dillo. Se la risposta non c'e', dillo.
Ogni affermazione della risposta deve poggiare su una citazione LETTERALE (copiata parola per parola) da una frase numerata.
JSON: {{"risposta": "max 70 parole", "certezza": "confermato|riportato|contestato|non_si_sa", "citazioni": [{{"n": 1, "citazione": "..."}}]}}""",
            tier="fast",
            max_tokens=600,
            required_keys=("risposta", "citazioni"),
        )
    except Exception as e:
        log.warning("Risposta LLM fallita: %s", e)
        return None
    cits = []
    for c in data.get("citazioni") or []:
        try:
            cand = candidates[int(c.get("n")) - 1]
        except (TypeError, ValueError, IndexError):
            continue
        art = by_id.get(cand.article_id)
        quote = (c.get("citazione") or "").strip()
        if not art or not quote:
            continue
        ok, _ = verify(quote, art)
        cits.append(cand.model_copy(update={"text": quote, "verified": ok}))
    if not any(c.verified for c in cits):
        return None
    certainty = data.get("certezza") if data.get("certezza") in ("confermato", "riportato", "contestato", "non_si_sa") else None
    return AnswerResult(
        question=question,
        answer=(data.get("risposta") or "").strip(),
        certainty=certainty,
        citations=[c for c in cits if c.verified],
        method="modello+citazioni verificate",
    )
