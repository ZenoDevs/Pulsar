"""Il dossier: separare i fatti dalle interpretazioni.

Flusso:
1. Il modello legge gli articoli numerati e produce un JSON strutturato
   (fatti con stato, interpretazioni, divergenze, inquadramenti, omissioni,
   linguaggio carico, domande aperte).
2. Le citazioni [n] vengono mappate su articoli e testate reali; quelle
   inventate vengono scartate.
3. Regole deterministiche e *conservative* correggono il modello: uno stato
   puo' solo essere abbassato, mai alzato. Un "confermato" sostenuto da una
   sola voce indipendente (stesso editore o ripresa d'agenzia) diventa
   "riportato", e la nota spiega perche'.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Dict, List, Optional

from .. import llm
from ..schemas import (
    Article,
    Divergence,
    Dossier,
    Evidence,
    Fact,
    Framing,
    Interpretation,
    LoadedTerm,
    Omission,
    Version,
)
from ..sources import get_source, is_agency, owner_group_of
from .grounding import verify
from .independence import independent_voices

log = logging.getLogger("pulsar.dossier")

PROMPT_VERSION = "dossier-v3"
MAX_ARTICLES = 18
CHARS_PER_ARTICLE = 1400
STATUSES = ("confermato", "riportato", "contestato", "non_verificato")
INTERP_KINDS = ("opinione", "previsione", "causa", "giudizio", "attribuzione")

SYSTEM = """Sei il desk di verifica di Pulsar, una testata che non prende posizione: mostra cosa e' accertato, cosa e' solo riportato, dove le fonti si contraddicono e come ciascuna inquadra i fatti.
Lavori SOLO sugli articoli forniti. Non aggiungere fatti dalla tua memoria: se qualcosa non e' negli articoli, non esiste per questo dossier.
Scrivi in italiano piano, frasi brevi, senza aggettivi valutativi. Rispondi solo con JSON valido."""

PROMPT = """Articoli sullo stesso fatto (il numero tra parentesi quadre e' l'identificativo da citare):

{articles}

Costruisci il dossier. Definizioni da rispettare alla lettera:
- FATTO: affermazione verificabile su cosa e' successo (chi, cosa, quando, dove, quanto). Una affermazione per voce, atomica.
  - "confermato": riportato in modo concorde da almeno due testate che NON si limitano a copiare lo stesso testo.
  - "riportato": lo dice una sola testata, o tutte citano la stessa unica fonte (es. un comunicato, "secondo fonti").
  - "contestato": le testate danno versioni incompatibili (numeri diversi, dinamiche diverse) o una parte lo smentisce.
  - "non_verificato": attribuito a fonti anonime, indiscrezioni, "secondo quanto si apprende", o non verificabile.
- INTERPRETAZIONE: tutto cio' che non e' un fatto: opinioni, previsioni, attribuzioni di causa o responsabilita', giudizi morali. Indica chi la sostiene.
- DIVERGENZA: un punto su cui le testate raccontano cose diverse. Riporta ogni versione con le sue fonti.
- INQUADRAMENTO: la cornice narrativa di un gruppo di testate (es. "questione di ordine pubblico" vs "questione di diritti"), con le parole chiave che la rivelano.
- OMISSIONE: un elemento rilevante presente in alcune testate e assente in altre. Usa i nomi delle testate.
- LINGUAGGIO CARICO: termini emotivi o di parte usati da una testata, con un'alternativa neutra.
- DOMANDE APERTE: cosa non si sa ancora e servirebbe sapere.

Ogni fatto, interpretazione e versione DEVE citare gli articoli con i loro numeri. Non citare numeri che non esistono.
Per ogni fatto aggiungi in "evidenze" una citazione LETTERALE (6-25 parole, copiata parola per parola) da ciascun articolo citato. Le citazioni vengono controllate automaticamente: se non si trovano nel testo, il fatto viene declassato.

JSON:
{{
  "titolo_neutro": "max 14 parole, soggetto-verbo-fatto",
  "sezione": "Politica|Esteri|Economia|Cronaca|Società|Cultura|Scienza|Sport",
  "sommario": "2-3 frasi con solo cio' che e' confermato",
  "fatti": [{{"testo": "...", "stato": "confermato|riportato|contestato|non_verificato", "fonti": [1, 3], "evidenze": [{{"fonte": 1, "citazione": "..."}}, {{"fonte": 3, "citazione": "..."}}], "nota": "opzionale, max 20 parole"}}],
  "interpretazioni": [{{"testo": "...", "tipo": "opinione|previsione|causa|giudizio|attribuzione", "fonti": [2]}}],
  "divergenze": [{{"tema": "...", "versioni": [{{"racconto": "...", "fonti": [1]}}, {{"racconto": "...", "fonti": [4]}}]}}],
  "inquadramenti": [{{"etichetta": "max 5 parole", "cornice": "una frase", "parole_chiave": ["..."], "fonti": [2, 5]}}],
  "omissioni": [{{"elemento": "...", "presente_in": [1, 2], "assente_in": [4]}}],
  "linguaggio": [{{"termine": "...", "fonte": 4, "alternativa_neutra": "...", "perche": "max 15 parole"}}],
  "domande_aperte": ["..."],
  "contesto": "2 frasi di contesto SOLO se ricavabili dagli articoli, altrimenti stringa vuota"
}}"""


def format_articles(articles: List[Article]) -> str:
    out = []
    for i, a in enumerate(articles, 1):
        src = get_source(a.source_id)
        kind = f", {src.kind}" if src else ""
        when = a.published_at.strftime("%d/%m %H:%M") if a.published_at else "ora n.d."
        text = (a.body or a.snippet or "").replace("\n", " ").strip()[:CHARS_PER_ARTICLE]
        out.append(f"[{i}] {a.source_name}{kind} — {when}\nTitolo: {a.title}\nTesto: {text}")
    return "\n\n".join(out)


def select_articles(articles: List[Article], limit: int = MAX_ARTICLES) -> List[Article]:
    """Sceglie gli articoli da mandare al modello: prima uno per testata
    (privilegiando testi originali e lunghi), poi il resto."""
    originals = sorted(articles, key=lambda a: (bool(a.echo_of), -len(a.body or a.snippet or "")))
    picked, seen = [], set()
    for a in originals:
        if a.source_id not in seen:
            picked.append(a)
            seen.add(a.source_id)
    picked_ids = {a.id for a in picked}
    for a in originals:
        if len(picked) >= limit:
            break
        if a.id not in picked_ids and not a.echo_of:
            picked.append(a)
            picked_ids.add(a.id)
    return picked[:limit]


# --------------------------------------------------------------------------
# Parsing + regole
# --------------------------------------------------------------------------


def _refs(raw, idx: Dict[int, Article]) -> List[Article]:
    if raw is None:
        return []
    if isinstance(raw, (int, str)):
        raw = [raw]
    out = []
    for r in raw:
        try:
            n = int(str(r).strip("[] "))
        except ValueError:
            continue
        if n in idx and idx[n] not in out:
            out.append(idx[n])
    return out


def _ids(arts: List[Article]):
    return [a.id for a in arts], list(dict.fromkeys(a.source_id for a in arts))


def apply_rules(fact: Fact, cited: List[Article], universe: Dict[str, Article]) -> Fact:
    """Regole conservative: possono solo abbassare lo stato."""
    voices = independent_voices(cited, universe)
    fact.independent_voices = voices
    groups = {owner_group_of(a.source_id) for a in cited}

    if not cited:
        fact.downgraded_from = fact.status if fact.status != "non_verificato" else None
        fact.status = "non_verificato"
        fact.verification = "Nessun articolo citato a supporto."
        return fact

    if fact.status == "confermato" and voices < 2:
        fact.downgraded_from = "confermato"
        fact.status = "riportato"
        if len(cited) > 1 and len(groups) == 1:
            fact.verification = "Lo riportano piu' testate, ma tutte dello stesso editore: conta come una voce."
        elif len(cited) > 1:
            fact.verification = "Lo riportano piu' testate, ma riprendono lo stesso testo: conta come una voce."
        else:
            fact.verification = "Una sola testata lo riporta."
        return fact

    if fact.status == "confermato":
        agency_only = all(is_agency(a.source_id) or a.echo_of for a in cited)
        fact.verification = (
            f"{voices} voci indipendenti" + (" (in parte riprese d'agenzia)" if agency_only else "") + "."
        )
    elif fact.status == "riportato":
        fact.verification = f"{voices} voce indipendente." if voices == 1 else f"{voices} voci, ma da una fonte unica a monte."
    elif fact.status == "contestato":
        fact.verification = "Versioni incompatibili tra le testate."
    else:
        fact.verification = "Attribuito a fonti non identificate o non verificabile."
    return fact


def ground(raw_evidence, cited: List[Article], idx: Dict[int, Article]):
    """Verifica le citazioni. Restituisce (evidenze, articoli ancora validi, articoli respinti).

    Se il modello non ha fornito citazioni (es. vecchi dossier, demo), non si
    respinge nulla: l'ancoraggio si applica solo dove c'e' qualcosa da verificare.
    """
    evidence: List[Evidence] = []
    if not raw_evidence:
        return evidence, cited, []
    quoted: Dict[str, bool] = {}
    for ev in raw_evidence:
        if not isinstance(ev, dict):
            continue
        arts = _refs(ev.get("fonte"), idx)
        quote = (ev.get("citazione") or "").strip()
        if not arts or not quote:
            continue
        a = arts[0]
        ok, m = verify(quote, a)
        evidence.append(Evidence(article_id=a.id, source_id=a.source_id, quote=quote, verified=ok, match=m))
        quoted[a.id] = quoted.get(a.id, False) or ok
    rejected = [a for a in cited if a.id in quoted and not quoted[a.id]]
    kept = [a for a in cited if a not in rejected]
    return evidence, kept, rejected


def input_hash(articles: List[Article]) -> str:
    raw = "|".join(f"{a.id}:{len(a.body or a.snippet or '')}" for a in articles)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def parse_dossier(data: dict, selected: List[Article], universe: Dict[str, Article]) -> Dossier:
    idx = {i: a for i, a in enumerate(selected, 1)}
    grounding_ok = grounding_tot = 0

    facts: List[Fact] = []
    for n, f in enumerate(data.get("fatti") or [], 1):
        text = (f.get("testo") or "").strip()
        if not text:
            continue
        status = f.get("stato") if f.get("stato") in STATUSES else "non_verificato"
        cited = _refs(f.get("fonti"), idx)
        evidence, cited, rejected = ground(f.get("evidenze"), cited, idx)
        grounding_tot += len(evidence)
        grounding_ok += sum(1 for e in evidence if e.verified)
        aids, sids = _ids(cited)
        fact = Fact(
            id=f"F{n}", text=text, status=status, article_ids=aids, source_ids=sids,
            note=f.get("nota") or None, evidence=evidence,
        )
        fact = apply_rules(fact, cited, universe)
        if rejected and not cited:
            fact.downgraded_from = fact.downgraded_from or (status if status != "non_verificato" else None)
            fact.status = "non_verificato"
            fact.verification = "Le citazioni indicate dal modello non si ritrovano negli articoli."
        elif rejected:
            fact.verification = (fact.verification or "") + f" {len(rejected)} citazione non ritrovata: fonte esclusa."
        facts.append(fact)

    interps = []
    for it in data.get("interpretazioni") or []:
        cited = _refs(it.get("fonti"), idx)
        if not it.get("testo"):
            continue
        aids, sids = _ids(cited)
        kind = it.get("tipo") if it.get("tipo") in INTERP_KINDS else "opinione"
        interps.append(Interpretation(text=it["testo"].strip(), kind=kind, article_ids=aids, source_ids=sids))

    divs = []
    for d in data.get("divergenze") or []:
        versions = []
        for v in d.get("versioni") or []:
            cited = _refs(v.get("fonti"), idx)
            if v.get("racconto") and cited:
                aids, sids = _ids(cited)
                versions.append(Version(account=v["racconto"].strip(), article_ids=aids, source_ids=sids))
        if d.get("tema") and len(versions) >= 2:
            divs.append(Divergence(topic=d["tema"].strip(), versions=versions))

    framings = []
    for fr in data.get("inquadramenti") or []:
        cited = _refs(fr.get("fonti"), idx)
        if not fr.get("cornice") or not cited:
            continue
        aids, sids = _ids(cited)
        framings.append(
            Framing(
                label=(fr.get("etichetta") or "").strip() or "Inquadramento",
                frame=fr["cornice"].strip(),
                keywords=[k for k in (fr.get("parole_chiave") or []) if isinstance(k, str)][:6],
                source_ids=sids,
                article_ids=aids,
            )
        )
    # Ordina gli inquadramenti da sinistra a destra, come lo spettro
    def _mean_or(fr: Framing) -> float:
        vals = [get_source(s).orientation for s in fr.source_ids if get_source(s)]
        return sum(vals) / len(vals) if vals else 0.0

    framings.sort(key=_mean_or)

    omissions = []
    for o in data.get("omissioni") or []:
        present = _ids(_refs(o.get("presente_in"), idx))[1]
        absent = _ids(_refs(o.get("assente_in"), idx))[1]
        absent = [s for s in absent if s not in present]
        if o.get("elemento") and present and absent:
            omissions.append(Omission(element=o["elemento"].strip(), present_in=present, absent_in=absent))

    loaded = []
    for t in data.get("linguaggio") or []:
        cited = _refs(t.get("fonte"), idx)
        if not t.get("termine") or not t.get("alternativa_neutra"):
            continue
        a = cited[0] if cited else None
        loaded.append(
            LoadedTerm(
                term=t["termine"].strip(),
                neutral=t["alternativa_neutra"].strip(),
                why=(t.get("perche") or "").strip(),
                article_id=a.id if a else None,
                source_id=a.source_id if a else None,
            )
        )

    return Dossier(
        neutral_title=(data.get("titolo_neutro") or "").strip() or selected[0].title,
        summary=(data.get("sommario") or "").strip(),
        facts=facts,
        interpretations=interps,
        divergences=divs,
        framings=framings,
        omissions=omissions,
        loaded_language=loaded,
        open_questions=[q.strip() for q in (data.get("domande_aperte") or []) if isinstance(q, str) and q.strip()],
        context=(data.get("contesto") or "").strip() or None,
        section=(data.get("sezione") or "").strip() or None,
        generated_by=f"{llm.provider() or 'n.d.'}",
        prompt_version=PROMPT_VERSION,
        input_hash=input_hash(selected),
        grounding={"verified": grounding_ok, "total": grounding_tot} if grounding_tot else None,
    )


def build_dossier(articles: List[Article]) -> Optional[Dossier]:
    """Genera il dossier di una storia. Restituisce None senza LLM o con meno
    di due articoli (non c'e' nulla da confrontare)."""
    if not llm.available() or len(articles) < 2:
        return None
    selected = select_articles(articles)
    universe = {a.id: a for a in articles}
    try:
        data = llm.complete_json(
            PROMPT.format(articles=format_articles(selected)),
            system=SYSTEM,
            tier="deep",
            max_tokens=6000,
            temperature=0.1,
            required_keys=("fatti", "titolo_neutro"),
        )
    except Exception as e:
        log.warning("Dossier non generato: %s", e)
        return None
    return parse_dossier(data, selected, universe)
