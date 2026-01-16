"""Main task orchestrating scheduled scraping workflow.

Flow:
1. Scrape all section pages in parallel
2. For each article:
   - Check if URL exists in DB
   - If exists: extract keywords and update only keywords
   - If not exists: scrape full text, extract keywords, save everything
3. Save keywords as SearchQuery relations
"""

import asyncio
from datetime import datetime
from typing import List
from concurrent.futures import ThreadPoolExecutor

from ..db.orm import (
    SessionLocal,
    ArticleModel,
    SearchQuery,
    get_article_by_url,
)
from ..infrastructure.scrapers.news_scrapers import scrape_full_text
from .scrapers import scrape_all
from .keyword_extractor import extract_keywords, is_extractor_available


def _process_article(article_data: dict) -> dict:
    """
    Process a single article: check DB, scrape if needed, extract keywords.
    
    Returns dict with processing result.
    """
    url = article_data.get("url")
    if not url:
        return {"status": "skipped", "reason": "no_url"}
    
    with SessionLocal() as db:
        # Check if article exists in DB
        existing = get_article_by_url(db, url)
        
        if existing:
            # Article exists - only extract and update keywords
            if is_extractor_available():
                keywords = extract_keywords(
                    title=existing.get("title", ""),
                    body=existing.get("body", ""),
                    snippet=existing.get("snippet", ""),
                )
                
                # Update keywords in DB
                if keywords:
                    _update_article_keywords(db, url, keywords)
                    return {
                        "status": "updated_keywords",
                        "url": url,
                        "keywords": keywords,
                    }
            
            return {"status": "skipped", "reason": "already_exists", "url": url}
        
        else:
            # New article - scrape full text, extract keywords, save
            body = scrape_full_text(url)
            
            # Extract keywords
            keywords = []
            if is_extractor_available():
                keywords = extract_keywords(
                    title=article_data.get("title", ""),
                    body=body,
                    snippet=article_data.get("snippet", ""),
                )
            
            # Save article to DB
            _save_new_article(db, article_data, body, keywords)
            
            return {
                "status": "created",
                "url": url,
                "keywords": keywords,
                "has_body": bool(body),
            }


def _update_article_keywords(db, url: str, keywords: List[str]):
    """Update only the keywords for an existing article."""
    try:
        article = db.query(ArticleModel).filter(ArticleModel.url == url).first()
        if not article:
            return
        
        for keyword in keywords:
            keyword = keyword.strip().lower()
            if not keyword:
                continue
            
            # Get or create SearchQuery
            search_query = db.query(SearchQuery).filter(SearchQuery.text == keyword).first()
            if not search_query:
                search_query = SearchQuery(
                    text=keyword,
                    count=1,
                    last_searched_at=datetime.utcnow(),
                )
                db.add(search_query)
            else:
                search_query.count += 1
                search_query.last_searched_at = datetime.utcnow()
            
            # Link to article if not already linked
            if search_query not in article.queries:
                article.queries.append(search_query)
            
            # Also update legacy JSON field
            current_queries = list(article.search_queries) if article.search_queries else []
            if keyword not in current_queries:
                current_queries.append(keyword)
                article.search_queries = current_queries
        
        db.commit()
        
    except Exception as e:
        print(f"[Tasks] Error updating keywords for {url}: {e}")
        db.rollback()


def _save_new_article(db, article_data: dict, body: str, keywords: List[str]):
    """Save a new article with its body and keywords."""
    try:
        # Parse published_at if it's a datetime object
        pub_at = article_data.get("published_at")
        if isinstance(pub_at, str):
            try:
                pub_at = datetime.fromisoformat(pub_at)
            except:
                pub_at = None
        
        # Create article
        article = ArticleModel(
            id=article_data.get("id", ""),
            url=article_data.get("url", ""),
            source_id=article_data.get("source_id", ""),
            title=article_data.get("title", ""),
            snippet=article_data.get("snippet", ""),
            body=body,
            published_at=pub_at,
            fetched_at=datetime.utcnow(),
            search_queries=[],
        )
        db.add(article)
        db.flush()  # Get the article in the session
        
        # Add keywords
        for keyword in keywords:
            keyword = keyword.strip().lower()
            if not keyword:
                continue
            
            # Get or create SearchQuery
            search_query = db.query(SearchQuery).filter(SearchQuery.text == keyword).first()
            if not search_query:
                search_query = SearchQuery(
                    text=keyword,
                    count=1,
                    last_searched_at=datetime.utcnow(),
                )
                db.add(search_query)
            else:
                search_query.count += 1
                search_query.last_searched_at = datetime.utcnow()
            
            # Link to article
            article.queries.append(search_query)
            
            # Also update legacy JSON field
            current_queries = list(article.search_queries) if article.search_queries else []
            if keyword not in current_queries:
                current_queries.append(keyword)
                article.search_queries = current_queries
        
        db.commit()
        
    except Exception as e:
        print(f"[Tasks] Error saving article {article_data.get('url')}: {e}")
        db.rollback()


def run_scheduled_scrape() -> dict:
    """
    Main synchronous entry point for scheduled scraping.
    
    Returns summary of scraping results.
    """
    print("[Scheduled Scrape] Starting...")
    start_time = datetime.utcnow()
    
    # 1. Scrape all sections
    articles = scrape_all()
    
    if not articles:
        print("[Scheduled Scrape] No articles found")
        return {
            "status": "completed",
            "articles_found": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }
    
    print(f"[Scheduled Scrape] Processing {len(articles)} articles...")
    
    # 2. Convert Article objects to dicts for processing
    article_dicts = []
    for art in articles:
        article_dicts.append({
            "id": art.id,
            "url": art.url,
            "source_id": art.source_id,
            "title": art.title,
            "snippet": art.snippet,
            "published_at": art.published_at,
        })
    
    # 3. Process articles in parallel
    results = {
        "created": 0,
        "updated_keywords": 0,
        "skipped": 0,
        "errors": 0,
    }
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_process_article, art) for art in article_dicts]
        
        for future in futures:
            try:
                result = future.result()
                status = result.get("status", "unknown")
                
                if status == "created":
                    results["created"] += 1
                elif status == "updated_keywords":
                    results["updated_keywords"] += 1
                elif status == "skipped":
                    results["skipped"] += 1
                else:
                    results["errors"] += 1
                    
            except Exception as e:
                print(f"[Scheduled Scrape] Error processing article: {e}")
                results["errors"] += 1
    
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    summary = {
        "status": "completed",
        "duration_seconds": duration,
        "articles_found": len(articles),
        **results,
    }
    
    print(f"[Scheduled Scrape] Completed in {duration:.1f}s: {summary}")
    return summary


async def run_scheduled_scrape_async() -> dict:
    """
    Async wrapper for the scheduled scrape task.
    Runs the synchronous scrape in a thread pool to avoid blocking.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_scheduled_scrape)
