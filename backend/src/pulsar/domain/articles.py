from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field  


class Article(BaseModel):
    """Normalized news article schema returned by the API."""

    id: str = Field(..., description="Unique ID for the article (hash)")
    source_id: str = Field(..., description="ID of the source outlet")
    source_name: str = Field(..., description="Human readable source name")

    # Bias fields
    bias: Literal["left", "center", "right", "unknown"] = Field(
        ..., description="Effective bias (fusion of source and article)"
    )
    bias_source: Optional[Literal["left", "center", "right", "unknown"]] = Field(
        None, description="Static bias of the source outlet"
    )
    bias_article: Optional[Literal["left", "center", "right", "unknown"]] = Field(
        None, description="AI-detected bias of the content"
    )
    bias_confidence: Optional[float] = Field(
        None, description="Confidence of the AI classification (0.0-1.0)"
    )
    bias_explanation: Optional[str] = Field(
        None, description="Short explanation of the AI classification"
    )

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
