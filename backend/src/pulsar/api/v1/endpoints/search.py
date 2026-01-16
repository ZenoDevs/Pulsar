import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException 

from ....domain import JobResponse, JobStatusResponse, SearchRequest
from ....core.state import jobs
from ....jobs.search_job import process_search_job

router = APIRouter()

@router.post("/search", response_model=JobResponse)
def search_news(payload: SearchRequest, background_tasks: BackgroundTasks) -> JobResponse:
    normalized_query = payload.query.strip().lower()

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "clusters": [], "message": "Starting..."}

    background_tasks.add_task(process_search_job, job_id, normalized_query, payload.start_date, payload.end_date)
    return JobResponse(job_id=job_id, status="pending")

@router.get("/search/status/{job_id}", response_model=JobStatusResponse)
def get_search_status(job_id: str) -> JobStatusResponse:
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        clusters=job["clusters"] if job["status"] == "completed" else None,
        message=job.get("message"),
    )
