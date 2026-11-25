from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

Leaning = Literal["left", "center", "right", "unknown"]
FactStatus = Literal["confermato", "riportato", "contestato", "non_verificato"]


class Article(BaseModel):
    """Articolo normalizzato."""

    id: str = Field(..., description="ID deterministico (hash)")
    source_id: str
    source_name: str

    # Bias: fascia effettiva + dettaglio
    bias: Leaning = Field(..., description="Fascia effettiva (fusione fonte + testo)")
    bias_source: Optional[Leaning] = None
    bias_article: Optional[Leaning] = None
    bias_confidence: Optional[float] = None
    bias_explanation: Optional[str] = None
    orientation_score: Optional[float] = Field(
        None, description="Posizione continua -1 (sinistra) .. +1 (destra)"
    )

    title: str
    snippet: str = ""
    body: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    published_at: Optional[datetime] = None
    raw_date: Optional[str] = None
    embedding: Optional[List[float]] = Field(None, exclude=True)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    # Calcolati a livello di storia
    echo_of: Optional[str] = Field(
        None, description="ID dell'articolo (di agenzia o precedente) di cui questo e' una ripresa"
    )
    echo_similarity: Optional[float] = None


class StoryStats(BaseModel):
    total_articles: int
    by_bias: Dict[str, int]
    by_source: Dict[str, int]
    first_published_at: Optional[datetime] = None
    last_published_at: Optional[datetime] = None


# --------------------------------------------------------------------------
# Dossier: la scomposizione epistemica di una storia
# --------------------------------------------------------------------------


class Fact(BaseModel):
    id: str
    text: str
    status: FactStatus
    article_ids: List[str] = []
    source_ids: List[str] = []
    independent_voices: int = 0
    note: Optional[str] = None
    verification: Optional[str] = Field(
        None, description="Spiegazione deterministica dello stato (regole di Pulsar)"
    )
    downgraded_from: Optional[FactStatus] = None


class Interpretation(BaseModel):
    text: str
    kind: Literal["opinione", "previsione", "causa", "giudizio", "attribuzione"] = "opinione"
    article_ids: List[str] = []
    source_ids: List[str] = []


class Version(BaseModel):
    account: str
    article_ids: List[str] = []
    source_ids: List[str] = []


class Divergence(BaseModel):
    topic: str
    versions: List[Version]


class Framing(BaseModel):
    label: str
    frame: str
    keywords: List[str] = []
    source_ids: List[str] = []
    article_ids: List[str] = []


class Omission(BaseModel):
    element: str
    present_in: List[str] = Field([], description="source_ids che lo riportano")
    absent_in: List[str] = Field([], description="source_ids che lo omettono")


class LoadedTerm(BaseModel):
    term: str
    neutral: str
    why: str = ""
    article_id: Optional[str] = None
    source_id: Optional[str] = None


class Dossier(BaseModel):
    neutral_title: str
    summary: str
    facts: List[Fact] = []
    interpretations: List[Interpretation] = []
    divergences: List[Divergence] = []
    framings: List[Framing] = []
    omissions: List[Omission] = []
    loaded_language: List[LoadedTerm] = []
    open_questions: List[str] = []
    context: Optional[str] = None
    section: Optional[str] = None
    generated_by: str = "ai"
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --------------------------------------------------------------------------
# Metriche di copertura
# --------------------------------------------------------------------------


class SpectrumPoint(BaseModel):
    source_id: str
    source_name: str
    orientation: float
    articles: int


class Independence(BaseModel):
    articles: int
    outlets: int
    owner_groups: int
    echoes: int = Field(..., description="Articoli che sono riprese quasi letterali di un altro")
    independent_voices: int


class Blindspot(BaseModel):
    side: Literal["left", "right"]
    message: str


class TimelineEntry(BaseModel):
    article_id: str
    source_id: str
    source_name: str
    title: str
    published_at: Optional[datetime] = None
    is_echo: bool = False


class StoryMetrics(BaseModel):
    spectrum: List[SpectrumPoint] = []
    leaning_share: Dict[str, float] = {}
    mean_orientation: Optional[float] = None
    independence: Independence
    blindspot: Optional[Blindspot] = None
    solidity: Optional[float] = Field(
        None, description="Quota di fatti confermati sul totale dei fatti (0-1)"
    )
    status_counts: Dict[str, int] = {}
    first_reported_by: Optional[str] = None
    timeline: List[TimelineEntry] = []


class Story(BaseModel):
    id: str
    query: str = ""
    title: str
    articles: List[Article]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    stats: StoryStats
    metrics: Optional[StoryMetrics] = None
    dossier: Optional[Dossier] = None
    score: float = 0.0
    section: Optional[str] = None
    # Retro-compatibilita': vecchia analisi markdown
    analysis: Optional[str] = None


class Headline(BaseModel):
    """Il titolo con cui una testata ha dato la notizia."""

    source_id: str
    source_name: str
    orientation: float
    title: str
    url: Optional[str] = None


class StorySummary(BaseModel):
    """Versione leggera per la prima pagina."""

    id: str
    title: str
    summary: Optional[str] = None
    section: Optional[str] = None
    stats: StoryStats
    metrics: Optional[StoryMetrics] = None
    key_facts: List[Fact] = []
    top_divergence: Optional[Divergence] = None
    headlines: List[Headline] = []
    loaded_terms: List[LoadedTerm] = []
    image_url: Optional[str] = None
    score: float = 0.0


class Edition(BaseModel):
    id: str
    generated_at: datetime
    demo: bool = False
    sources_ok: int = 0
    sources_total: int = 0
    articles_analyzed: int = 0
    stories: List[StorySummary] = []
    blindspots: List[StorySummary] = []


class SearchRequest(BaseModel):
    query: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
