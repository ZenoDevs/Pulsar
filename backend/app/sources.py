"""Registro delle fonti di Pulsar.

Ogni testata ha:
- ``orientation``: stima editoriale di partenza su un asse continuo
  -1.0 (sinistra) … 0 (centro) … +1.0 (destra). E' un punto di partenza
  dichiarato e contestabile: il bias del singolo articolo viene poi misurato
  sul testo (vedi services/openai_service.classify_bias).
- ``owner`` / ``owner_group``: chi controlla la testata. ``owner_group`` serve a
  calcolare le *voci indipendenti*: due testate dello stesso editore non
  contano come due conferme indipendenti.
- ``ownership_verified``: True solo per gli assetti verificati su fonti
  pubbliche (vedi ``ownership_source``). Tutto il resto e' marcato
  "da verificare" e l'interfaccia lo mostra come tale.
- ``feeds``: feed RSS. Gli URL vanno controllati al primo avvio con
  ``python -m app.cli check-feeds``: le testate cambiano spesso gli indirizzi.

Dati di proprieta' aggiornati a novembre 2026. Il mercato editoriale italiano
si e' mosso molto nel 2025-2026 (cessione GEDI, ingresso di Del Vecchio,
Domani passato a una fondazione): tenere questo file aggiornato e' parte del
prodotto, non un dettaglio.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

ORIENTATION_DISCLAIMER = (
    "Stima editoriale di partenza, non un giudizio definitivo: l'asse "
    "sinistra-destra semplifica molto e alcune testate (es. populiste o "
    "anti-establishment) non ci stanno bene. Il bias del singolo articolo "
    "viene misurato sul testo."
)


@dataclass(frozen=True)
class SourceInfo:
    id: str
    name: str
    kind: str  # agenzia | quotidiano | online | tv
    orientation: float
    owner: str
    owner_group: str
    homepage: str
    feeds: List[str] = field(default_factory=list)
    ownership_verified: bool = False
    ownership_source: Optional[str] = None
    note: Optional[str] = None

    @property
    def leaning(self) -> str:
        return leaning_from_score(self.orientation)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["leaning"] = self.leaning
        return d


def leaning_from_score(score: Optional[float]) -> str:
    """Mappa il punteggio continuo sulle tre fasce usate in UI."""
    if score is None:
        return "unknown"
    if score <= -0.25:
        return "left"
    if score >= 0.25:
        return "right"
    return "center"


_SOURCES: List[SourceInfo] = [
    # --- Agenzie -----------------------------------------------------------
    SourceInfo(
        id="ansa", name="ANSA", kind="agenzia", orientation=0.0,
        owner="Cooperativa di editori di quotidiani", owner_group="ansa-coop",
        homepage="https://www.ansa.it",
        feeds=["https://www.ansa.it/sito/ansait_rss.xml"],
        note="Agenzia: molti quotidiani ne riprendono i lanci quasi alla lettera. "
             "Pulsar individua queste riprese e non le conta come conferme indipendenti.",
    ),
    SourceInfo(
        id="agi", name="AGI", kind="agenzia", orientation=0.0,
        owner="Eni", owner_group="eni",
        homepage="https://www.agi.it",
        feeds=["https://www.agi.it/rss"],
        ownership_verified=True,
        ownership_source="https://www.eni.com/en-IT/company/subsidiaries-and-affiliates/agi.html",
        note="Agenzia controllata da Eni (societa' a partecipazione pubblica).",
    ),
    # --- Quotidiani nazionali ---------------------------------------------
    SourceInfo(
        id="corriere", name="Corriere della Sera", kind="quotidiano", orientation=0.05,
        owner="RCS MediaGroup (Urbano Cairo)", owner_group="cairo",
        homepage="https://www.corriere.it",
        feeds=["https://xml2.corriereobjects.it/rss/homepage.xml"],
        ownership_verified=True,
        ownership_source="https://www.ilpost.it/charlie/chi-sono-gli-editori-italiani-2/",
    ),
    SourceInfo(
        id="la_repubblica", name="La Repubblica", kind="quotidiano", orientation=-0.5,
        owner="Antenna Group (famiglia Kyriakou)", owner_group="antenna",
        homepage="https://www.repubblica.it",
        feeds=["https://www.repubblica.it/rss/homepage/rss2.0.xml"],
        ownership_verified=True,
        ownership_source="https://www.italiaoggi.it/marketing-e-media/media/gedi-ha-venduto-repubblica-il-quotidiano-ai-greci-kyriakou-j5ae9h3o",
        note="Ceduta da GEDI (Exor) al gruppo greco Antenna a marzo 2026.",
    ),
    SourceInfo(
        id="la_stampa", name="La Stampa", kind="quotidiano", orientation=-0.2,
        owner="Gruppo SAE (Alberto Leonardis)", owner_group="sae",
        homepage="https://www.lastampa.it",
        feeds=["https://www.lastampa.it/rss.xml"],
        ownership_verified=True,
        ownership_source="https://www.italiaoggi.it/marketing-e-media/media/gedi-vende-la-stampa-al-gruppo-sae-b4cw9h8f",
        note="Ceduta da GEDI al gruppo SAE nel 2026.",
    ),
    SourceInfo(
        id="sole24ore", name="Il Sole 24 Ore", kind="quotidiano", orientation=0.2,
        owner="Confindustria", owner_group="confindustria",
        homepage="https://www.ilsole24ore.com",
        feeds=["https://www.ilsole24ore.com/rss/italia.xml"],
        ownership_verified=True,
        ownership_source="https://www.ilpost.it/charlie/chi-sono-gli-editori-italiani-2/",
    ),
    SourceInfo(
        id="messaggero", name="Il Messaggero", kind="quotidiano", orientation=0.3,
        owner="Caltagirone Editore", owner_group="caltagirone",
        homepage="https://www.ilmessaggero.it",
        feeds=["https://www.ilmessaggero.it/rss/home.xml"],
        ownership_verified=True,
        ownership_source="https://www.ilpost.it/charlie/chi-sono-gli-editori-italiani-2/",
    ),
    SourceInfo(
        id="il_giornale", name="Il Giornale", kind="quotidiano", orientation=0.7,
        owner="Famiglia Angelucci (maggioranza) e LMDV Capital di L. M. Del Vecchio (30%)",
        owner_group="angelucci",
        homepage="https://www.ilgiornale.it",
        feeds=["https://www.ilgiornale.it/feed.xml"],
        ownership_verified=True,
        ownership_source="https://www.ilpost.it/2025/12/19/leonardo-maria-del-vecchio-il-giornale-angelucci/",
    ),
    SourceInfo(
        id="libero", name="Libero", kind="quotidiano", orientation=0.8,
        owner="Famiglia Angelucci", owner_group="angelucci",
        homepage="https://www.liberoquotidiano.it",
        feeds=["https://www.liberoquotidiano.it/rss.xml"],
        ownership_verified=True,
        ownership_source="https://www.ilpost.it/2025/12/19/leonardo-maria-del-vecchio-il-giornale-angelucci/",
    ),
    SourceInfo(
        id="il_tempo", name="Il Tempo", kind="quotidiano", orientation=0.7,
        owner="Famiglia Angelucci (maggioranza)", owner_group="angelucci",
        homepage="https://www.iltempo.it",
        feeds=["https://www.iltempo.it/rss.jsp"],
        ownership_verified=True,
        ownership_source="https://www.calcioefinanza.it/?p=193845",
    ),
    SourceInfo(
        id="la_verita", name="La Verità", kind="quotidiano", orientation=0.85,
        owner="La Verità srl", owner_group="la-verita",
        homepage="https://www.laverita.info",
        feeds=["https://www.laverita.info/feeds/feed.rss"],
    ),
    SourceInfo(
        id="fatto", name="Il Fatto Quotidiano", kind="quotidiano", orientation=-0.35,
        owner="Società Editoriale Il Fatto (SEIF)", owner_group="seif",
        homepage="https://www.ilfattoquotidiano.it",
        feeds=["https://www.ilfattoquotidiano.it/feed/"],
        note="Linea anti-establishment: l'asse sinistra-destra la descrive male.",
    ),
    SourceInfo(
        id="avvenire", name="Avvenire", kind="quotidiano", orientation=-0.1,
        owner="Conferenza Episcopale Italiana", owner_group="cei",
        homepage="https://www.avvenire.it",
        feeds=["https://www.avvenire.it/rss"],
    ),
    SourceInfo(
        id="manifesto", name="Il Manifesto", kind="quotidiano", orientation=-0.85,
        owner="Cooperativa dei giornalisti", owner_group="manifesto-coop",
        homepage="https://ilmanifesto.it",
        feeds=["https://ilmanifesto.it/feed"],
    ),
    SourceInfo(
        id="domani", name="Domani", kind="quotidiano", orientation=-0.5,
        owner="Fondazione (ex Carlo De Benedetti)", owner_group="domani",
        homepage="https://www.editorialedomani.it",
        feeds=["https://www.editorialedomani.it/rss"],
        note="Il controllo e' passato nel 2025 a una fondazione: dettagli da verificare.",
    ),
    SourceInfo(
        id="il_foglio", name="Il Foglio", kind="quotidiano", orientation=0.3,
        owner="Il Foglio quotidiano soc. coop.", owner_group="foglio",
        homepage="https://www.ilfoglio.it",
        feeds=["https://www.ilfoglio.it/rss.jsp"],
        ownership_verified=True,
        ownership_source="https://ilfoglio.it/static/2026/01/28/news/condizioni-duso-dei-servizi-offerti--2671",
    ),
    # --- Online -----------------------------------------------------------
    SourceInfo(
        id="il_post", name="Il Post", kind="online", orientation=-0.25,
        owner="Il Post srl", owner_group="il-post",
        homepage="https://www.ilpost.it",
        feeds=["https://www.ilpost.it/feed/"],
    ),
    SourceInfo(
        id="open", name="Open", kind="online", orientation=-0.15,
        owner="Gol srl impresa sociale (Enrico Mentana, 99%)", owner_group="mentana",
        homepage="https://www.open.online",
        feeds=["https://www.open.online/feed/"],
        ownership_verified=True,
        ownership_source="https://www.firstonline.info/?p=203721",
        note="Societa' senza scopo di lucro. Quote riferite alla fondazione (2018).",
    ),
    SourceInfo(
        id="fanpage", name="Fanpage", kind="online", orientation=-0.4,
        owner="Ciaopeople", owner_group="ciaopeople",
        homepage="https://www.fanpage.it",
        feeds=["https://www.fanpage.it/feed/"],
    ),
    # --- TV / servizio pubblico ------------------------------------------
    SourceInfo(
        id="rainews", name="RaiNews", kind="tv", orientation=0.1,
        owner="Rai (servizio pubblico)", owner_group="rai",
        homepage="https://www.rainews.it",
        feeds=["https://www.rainews.it/rss/ultimora"],
    ),
    SourceInfo(
        id="skytg24", name="Sky TG24", kind="tv", orientation=0.0,
        owner="Sky Italia (Comcast)", owner_group="comcast",
        homepage="https://tg24.sky.it",
        feeds=["https://tg24.sky.it/rss/tg24.xml"],
    ),
]

SOURCES: Dict[str, SourceInfo] = {s.id: s for s in _SOURCES}

# Retro-compatibilita' con il vecchio codice (scraper di ricerca).
SOURCE_NAMES: Dict[str, str] = {s.id: s.name for s in _SOURCES}
SOURCE_BIAS: Dict[str, str] = {s.id: s.leaning for s in _SOURCES}


def register_sources(extra: List[SourceInfo]) -> None:
    """Aggiunge fonti a runtime (usato dalla modalita' demo)."""
    for s in extra:
        SOURCES[s.id] = s
        SOURCE_NAMES[s.id] = s.name
        SOURCE_BIAS[s.id] = s.leaning


def get_source(source_id: str) -> Optional[SourceInfo]:
    return SOURCES.get(source_id)


def owner_group_of(source_id: str) -> str:
    s = SOURCES.get(source_id)
    return s.owner_group if s else f"unknown:{source_id}"


def is_agency(source_id: str) -> bool:
    s = SOURCES.get(source_id)
    return bool(s and s.kind == "agenzia")


def real_sources() -> List[SourceInfo]:
    return list(_SOURCES)
