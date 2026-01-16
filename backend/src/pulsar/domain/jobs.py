from typing import List, Optional

from pydantic import BaseModel  

from .clusters import Cluster


class JobResponse(BaseModel):
    """Response model for job creation."""

    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    """Response model for job status polling."""

    job_id: str
    status: str
    clusters: Optional[List[Cluster]] = None
    message: Optional[str] = None
