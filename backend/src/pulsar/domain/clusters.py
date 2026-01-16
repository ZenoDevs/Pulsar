from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field  

from .articles import Article


class ClusterStats(BaseModel):
    """Aggregated statistics for a cluster."""

    total_articles: int
    by_bias: Dict[str, int]  # keys: left, center, right, unknown
    by_source: Dict[str, int]
    first_published_at: Optional[datetime]
    last_published_at: Optional[datetime]


class Cluster(BaseModel):
    """A cluster of articles representing a single news event."""

    id: str
    query: str
    title: str
    articles: List[Article]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    stats: ClusterStats
    analysis: Optional[str] = Field(
        None, description="AI-generated analysis of the coverage and bias"
    )
