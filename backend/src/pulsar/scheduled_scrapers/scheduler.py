"""APScheduler configuration for scheduled scraping tasks."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..core.config import settings

# Global scheduler instance
_scheduler: AsyncIOScheduler = None


def get_scheduler() -> AsyncIOScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def start_scheduler():
    """
    Start the scheduler and register scheduled jobs.
    Should be called on FastAPI app startup.
    """
    global _scheduler
    
    # Import here to avoid circular imports
    from .tasks import run_scheduled_scrape_async
    
    _scheduler = get_scheduler()
    
    # Only start if not already running
    if _scheduler.running:
        print("[Scheduler] Already running, skipping start")
        return
    
    # Add the hourly scraping job
    _scheduler.add_job(
        run_scheduled_scrape_async,
        trigger=IntervalTrigger(hours=1),
        id="scheduled_scrape",
        name="Hourly News Scraping",
        replace_existing=True,
        # Run first job 30 seconds after startup
        next_run_time=None,  # Don't run immediately on startup
    )
    
    _scheduler.start()
    print("[Scheduler] Started with hourly scraping job")
    
    # Log next run time
    job = _scheduler.get_job("scheduled_scrape")
    if job:
        print(f"[Scheduler] Next scrape scheduled at: {job.next_run_time}")


def shutdown_scheduler():
    """
    Gracefully shutdown the scheduler.
    Should be called on FastAPI app shutdown.
    """
    global _scheduler
    
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("[Scheduler] Shutdown complete")


def trigger_scrape_now():
    """
    Manually trigger a scrape job immediately.
    Useful for testing or manual refresh.
    """
    from .tasks import run_scheduled_scrape_async
    import asyncio
    
    # Create a new event loop if needed
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # If we're already in an async context, schedule the task
        asyncio.create_task(run_scheduled_scrape_async())
    else:
        # Run synchronously
        loop.run_until_complete(run_scheduled_scrape_async())


def get_scheduler_status() -> dict:
    """Get current scheduler status for monitoring."""
    global _scheduler
    
    if not _scheduler:
        return {"running": False, "jobs": []}
    
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
        })
    
    return {
        "running": _scheduler.running,
        "jobs": jobs,
    }
