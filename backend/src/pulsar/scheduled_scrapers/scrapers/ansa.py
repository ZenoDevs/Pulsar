"""ANSA scraper for scheduled article collection."""

import re
from typing import List
from datetime import datetime

from .base import fetch_page, create_article, Article


# ANSA sections to scrape
SECTIONS = [
    "https://www.ansa.it/sito/notizie/topnews/index",
    "https://www.ansa.it/sito/notizie/politica/index",
    "https://www.ansa.it/sito/notizie/economia/index",
    "https://www.ansa.it/sito/notizie/mondo/index",
]

# Pages per section (ANSA has ~27 articles per page)
MAX_PAGES = 4

SOURCE_ID = "ansa"


def _scrape_page(url: str) -> List[dict]:
    """Scrape a single ANSA page."""
    articles = []
    
    soup = fetch_page(url)
    if not soup:
        return articles
    
    # ANSA uses h2/h3 with links
    headings = soup.find_all(["h2", "h3"])
    
    for heading in headings:
        try:
            a_tag = heading.find("a")
            if not a_tag:
                continue
            
            href = a_tag.get("href", "")
            
            # Filter for article URLs
            if not href or "/notizie/" not in href or not href.endswith(".html"):
                continue
            
            # Normalize URL
            if href.startswith("/"):
                href = "https://www.ansa.it" + href
            
            title = heading.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            
            # Extract snippet and date from parent container
            snippet = ""
            date_str = None
            
            parent = heading.parent
            if parent:
                # ANSA uses div.summary for snippets
                summary_div = parent.find("div", class_="summary")
                if summary_div:
                    snippet = summary_div.get_text(strip=True)
                
                # Fallback: look for other divs
                if not snippet:
                    divs = parent.find_all("div", recursive=False)
                    for div in divs:
                        div_text = div.get_text(strip=True)
                        if not div_text:
                            continue
                        
                        # Check if it's a date
                        if re.search(r"\d{1,2}:\d{2}", div_text) or any(
                            m in div_text.lower() for m in [
                                "gennaio", "febbraio", "marzo", "aprile",
                                "maggio", "giugno", "luglio", "agosto",
                                "settembre", "ottobre", "novembre", "dicembre"
                            ]
                        ):
                            date_str = div_text
                        elif len(div_text) > 20 and not snippet:
                            snippet = div_text
            
            articles.append({
                "title": title,
                "snippet": snippet,
                "url": href,
                "date_str": date_str,
            })
            
        except Exception:
            continue
    
    return articles


def _scrape_section(base_url: str, max_pages: int = MAX_PAGES) -> List[dict]:
    """Scrape multiple pages of an ANSA section."""
    all_articles = []
    seen_urls = set()
    
    for page in range(1, max_pages + 1):
        # ANSA pagination: index.shtml, index_2.shtml, index_3.shtml, etc.
        if page == 1:
            url = f"{base_url}.shtml"
        else:
            url = f"{base_url}_{page}.shtml"
        
        articles = _scrape_page(url)
        
        for art in articles:
            if art["url"] not in seen_urls:
                seen_urls.add(art["url"])
                all_articles.append(art)
        
        if not articles:
            break
    
    return all_articles


def _parse_ansa_date(date_str: str) -> datetime | None:
    """Parse ANSA date format: '16 gennaio 2026 - 22:16'"""
    if not date_str:
        return None
    
    try:
        match = re.search(
            r"(\d{1,2})\s+(\w+)\s+(\d{4})\s*-?\s*(\d{1,2}):(\d{2})",
            date_str
        )
        if match:
            day, month_str, year, hour, minute = match.groups()
            months = {
                "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
                "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
                "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12
            }
            month = months.get(month_str.lower(), 1)
            return datetime(int(year), month, int(day), int(hour), int(minute))
    except:
        pass
    
    return None


def scrape() -> List[Article]:
    """Scrape all ANSA sections and return Article objects."""
    articles = []
    seen_urls = set()
    
    for section_url in SECTIONS:
        raw_articles = _scrape_section(section_url)
        for raw in raw_articles:
            if raw["url"] in seen_urls:
                continue
            seen_urls.add(raw["url"])
            
            article = create_article(
                source_id=SOURCE_ID,
                title=raw["title"],
                url=raw["url"],
                snippet=raw.get("snippet", ""),
                published_at=_parse_ansa_date(raw.get("date_str")),
                raw_date=raw.get("date_str"),
            )
            articles.append(article)
    
    print(f"[ANSA] Scraped {len(articles)} articles from {len(SECTIONS)} sections")
    return articles
