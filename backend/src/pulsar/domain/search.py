from typing import List, Optional

from pydantic import BaseModel, Field  

from .clusters import Cluster


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
    """Response model containing clustered results."""

    query: str
    clusters: List[Cluster]
