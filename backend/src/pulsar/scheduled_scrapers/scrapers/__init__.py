"""Scheduled scrapers for Italian news sources."""

from typing import List
from concurrent.futures import ThreadPoolExecutor

from ...domain import Article

from . import repubblica
from . import ansa
from . import giornale


def scrape_all() -> List[Article]:
    """Scrape all sources in parallel and return combined list of articles."""
    all_articles: List[Article] = []
    
    print("[Scheduled Scrapers] Starting...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_repubblica = executor.submit(repubblica.scrape)
        future_ansa = executor.submit(ansa.scrape)
        future_giornale = executor.submit(giornale.scrape)
        
        try:
            all_articles.extend(future_repubblica.result())
        except Exception as e:
            print(f"[Scheduled Scrapers] Repubblica error: {e}")
        
        try:
            all_articles.extend(future_ansa.result())
        except Exception as e:
            print(f"[Scheduled Scrapers] ANSA error: {e}")
        
        try:
            all_articles.extend(future_giornale.result())
        except Exception as e:
            print(f"[Scheduled Scrapers] Il Giornale error: {e}")
    
    print(f"[Scheduled Scrapers] Total: {len(all_articles)} articles")
    return all_articles


__all__ = [
    "repubblica",
    "ansa", 
    "giornale",
    "scrape_all",
]
