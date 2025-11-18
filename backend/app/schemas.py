from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    """News source metadata."""

    id: str
    name: str
    bias: Literal["left", "center", "right", "unknown"]
    website: Optional[str] = None


class Article(BaseModel):
    """Normalized news article schema returned by the API."""

    id: str = Field(..., description="Unique ID for the article (hash)")
    source_id: str = Field(..., description="ID of the source outlet")
    source_name: str = Field(..., description="Human readable source name")
    
    # Bias fields
    bias: Literal["left", "center", "right", "unknown"] = Field(..., description="Effective bias (fusion of source and article)")
    bias_source: Optional[Literal["left", "center", "right", "unknown"]] = Field(None, description="Static bias of the source outlet")
    bias_article: Optional[Literal["left", "center", "right", "unknown"]] = Field(None, description="AI-detected bias of the content")
    bias_confidence: Optional[float] = Field(None, description="Confidence of the AI classification (0.0-1.0)")
    bias_explanation: Optional[str] = Field(None, description="Short explanation of the AI classification")

    title: str
    snippet: str
    body: Optional[str] = None
    url: Optional[str] = Field(None, description="URL of the article, if available")
    published_at: Optional[datetime] = Field(
        None, description="Normalized publication datetime, if available"
    )
    raw_date: Optional[str] = Field(
        None, description="Original date string as scraped, for debugging"
    )
    embedding: Optional[List[float]] = Field(
        None, description="Vector embedding of the article"
    )
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the article was fetched by Pulsar backend",
    )


class StoryStats(BaseModel):
    """Aggregated statistics for a story."""

    total_articles: int
    by_bias: Dict[str, int]  # keys: left, center, right, unknown
    by_source: Dict[str, int]
    first_published_at: Optional[datetime]
    last_published_at: Optional[datetime]


class Story(BaseModel):
    """A cluster of articles representing a single news event."""

    id: str
    query: str
    title: str
    articles: List[Article]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    stats: StoryStats
    analysis: Optional[str] = Field(None, description="AI-generated analysis of the coverage and bias")


class SearchRequest(BaseModel):
    """Search parameters posted by the client UI."""

    query: str = Field(..., description="User search query / topic keyword")
    start_date: Optional[str] = Field(
        None, description="Optional start date filter in YYYY-MM-DD format"
    )
    end_date: Optional[str] = Field(
        None, description="Optional end date filter in YYYY-MM-DD format"
    )


class SearchResponse(BaseModel):
    """Response model containing clustered stories."""

    query: str
    stories: List[Story]
