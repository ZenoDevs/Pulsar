from typing import Dict, Optional
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .clustering import cluster_articles_into_stories
from .schemas import SearchRequest, SearchResponse, Story, Article
from .scrapers.news_scrapers import fetch_articles_from_all_sources, SOURCE_NAMES, SOURCE_BIAS
from .services.openai_service import analyze_story_coverage, is_ai_available
from .db import search_articles_in_db

app = FastAPI(
    title="Pulsar API",
    description="News narrative intelligence backend for Italian news sources.",
    version="0.1.0",
)


# CORS: during development allow frontend on localhost (Vite default 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory cache for stories (MVP only)
stories_cache: Dict[str, Story] = {}

# Job management
jobs: Dict[str, Dict] = {}

class JobResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    stories: Optional[list[Story]] = None
    message: Optional[str] = None


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


def process_search_job(job_id: str, query: str, start_date: Optional[str], end_date: Optional[str]):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Searching local DB and external sources..."
        
        # 1. Local DB Search (Historical/Cached)
        local_results = search_articles_in_db(query, start_date, end_date)
        local_articles = []
        for r in local_results:
            try:
                s_id = r["source_id"]
                # Fallback for source name/bias if not in map
                s_name = SOURCE_NAMES.get(s_id, s_id)
                # Bias from analysis table takes precedence, else from source default
                bias = r["bias"] if r["bias"] else SOURCE_BIAS.get(s_id, "unknown")
                
                a = Article(
                    id=r["id"],
                    source_id=s_id,
                    source_name=s_name,
                    bias=bias,
                    bias_source=SOURCE_BIAS.get(s_id, "unknown"),
                    bias_article=r["bias_article"],
                    bias_confidence=r["bias_confidence"],
                    bias_explanation=r["bias_explanation"],
                    title=r["title"],
                    snippet=r["snippet"] or "",
                    body=r["body"],
                    url=r["url"],
                    published_at=r["published_at"], 
                    embedding=r["embedding"]
                )
                local_articles.append(a)
            except Exception as ex:
                print(f"Error reconstructing article from DB: {ex}")
                continue

        print(f"Found {len(local_articles)} articles in local DB.")

        # 2. Fetch articles from all sources (Live)
        # This will also enrich them (scrape body if new, load body from DB if known)
        live_articles = fetch_articles_from_all_sources(
            query=query,
            start_date=start_date,
            end_date=end_date,
        )

        # 3. Merge Results
        # We use a dictionary keyed by URL to deduplicate.
        # Live articles take precedence as they might have fresher metadata or we just want to confirm they are still online.
        # However, local articles might have bodies that live ones don't if scraping failed? 
        # Actually fetch_articles_from_all_sources handles the body loading.
        
        merged_map = {a.url: a for a in local_articles if a.url}
        
        for a in live_articles:
            if a.url:
                merged_map[a.url] = a
        
        # Convert back to list
        all_articles = list(merged_map.values())
        
        jobs[job_id]["message"] = f"Clustering {len(all_articles)} articles..."
        
        # 4. Cluster articles into stories
        stories = cluster_articles_into_stories(query, all_articles)

        # 5. Cache stories for detail view
        for story in stories:
            stories_cache[story.id] = story

        jobs[job_id]["stories"] = stories
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["message"] = "Done"
        
    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = str(e)


@app.post("/api/search", response_model=JobResponse)
def search_news(payload: SearchRequest, background_tasks: BackgroundTasks) -> JobResponse:
    """
    Initiates a background search job.
    Returns a job_id to poll for results.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "stories": [],
        "message": "Starting..."
    }
    
    background_tasks.add_task(
        process_search_job, 
        job_id, 
        payload.query, 
        payload.start_date, 
        payload.end_date
    )
    
    return JobResponse(job_id=job_id, status="pending")


@app.get("/api/search/status/{job_id}", response_model=JobStatusResponse)
def get_search_status(job_id: str) -> JobStatusResponse:
    """Check the status of a search job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        stories=job["stories"] if job["status"] == "completed" else None,
        message=job.get("message")
    )


@app.get("/api/story/{story_id}", response_model=Story)
def get_story_detail(story_id: str) -> Story:
    """Get full details of a specific story. Generates analysis if missing."""
    if story_id not in stories_cache:
        raise HTTPException(status_code=404, detail="Story not found")
    
    story = stories_cache[story_id]
    
    # Generate analysis on demand if missing and AI is available
    if not story.analysis and is_ai_available():
        # This might take a few seconds, blocking the response. 
        # For better UX in production, this should be async/background, 
        # but for MVP blocking is acceptable to ensure data is there.
        story.analysis = analyze_story_coverage(story.articles)
        # Update cache
        stories_cache[story_id] = story
        
    return story


# Placeholder for future RAG/chat module
@app.post("/api/chat")
def chat_placeholder():
    return {"detail": "Chat endpoint not implemented yet. Coming soon."}
