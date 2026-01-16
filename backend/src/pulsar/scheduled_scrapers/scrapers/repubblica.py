"""La Repubblica scraper for scheduled article collection."""

from typing import List
from datetime import datetime

from .base import fetch_page, create_article, Article


# All Repubblica sections to scrape
SECTIONS = [
    "https://www.repubblica.it/politica/",
    "https://www.repubblica.it/esteri/",
    "https://www.repubblica.it/cronaca/",
    "https://www.repubblica.it/economia/",
    "https://www.repubblica.it/tecnologia/",
]

# Pages per section
MAX_PAGES = 2

SOURCE_ID = "la_repubblica"


def _scrape_page(url: str) -> List[dict]:
    """Scrape a single Repubblica page."""
    articles = []
    
    soup = fetch_page(url)
    if not soup:
        return articles
    
    # Find all article elements
    article_elements = soup.find_all("article")
    
    for article in article_elements:
        try:
            # Find heading (h1, h2, or h3)
            heading = article.find(["h1", "h2", "h3"])
            if not heading:
                continue
            
            # Find link
            a_tag = heading.find("a")
            if not a_tag:
                a_tag = article.find("a")
            if not a_tag:
                continue
            
            title = heading.get_text(strip=True)
            link = a_tag.get("href", "")
            
            if not title or not link or len(title) < 10:
                continue
            
            # Normalize URL
            if link.startswith("/"):
                link = "https://www.repubblica.it" + link
            
            if not link.startswith("http"):
                continue
            
            # Extract snippet - Repubblica uses <p> inside <a> links
            snippet = ""
            
            # First try: paragraph inside links
            desc_links = article.find_all("a")
            for desc_link in desc_links:
                desc_p = desc_link.find("p")
                if desc_p:
                    desc_text = desc_p.get_text(strip=True)
                    if len(desc_text) > 30:
                        snippet = desc_text
                        break
            
            # Second try: any <p> tag with substantial text
            if not snippet:
                p_tags = article.find_all("p")
                for p in p_tags:
                    p_text = p.get_text(strip=True)
                    if len(p_text) > 30 and not p_text.startswith("di "):
                        snippet = p_text
                        break
            
            # Extract date
            date_str = None
            time_tag = article.find("time")
            if time_tag:
                date_str = time_tag.get("datetime") or time_tag.get_text(strip=True)
            
            articles.append({
                "title": title,
                "snippet": snippet,
                "url": link,
                "date_str": date_str,
            })
            
        except Exception:
            continue
    
    return articles


def _scrape_section(base_url: str, max_pages: int = MAX_PAGES) -> List[dict]:
    """Scrape multiple pages of a section."""
    all_articles = []
    seen_urls = set()
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = base_url
        else:
            if "?" in base_url:
                url = f"{base_url}&page={page}"
            else:
                url = f"{base_url}?page={page}"
        
        articles = _scrape_page(url)
        
        for art in articles:
            if art["url"] not in seen_urls:
                seen_urls.add(art["url"])
                all_articles.append(art)
        
        if not articles:
            break
    
    return all_articles


def scrape() -> List[Article]:
    """Scrape all Repubblica sections and return Article objects."""
    articles = []
    seen_urls = set()
    
    for section_url in SECTIONS:
        raw_articles = _scrape_section(section_url)
        for raw in raw_articles:
            if raw["url"] in seen_urls:
                continue
            seen_urls.add(raw["url"])
            
            # Parse date if available
            published_at = None
            if raw.get("date_str"):
                try:
                    date_str = raw["date_str"]
                    if "T" in date_str:
                        published_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    pass
            
            article = create_article(
                source_id=SOURCE_ID,
                title=raw["title"],
                url=raw["url"],
                snippet=raw.get("snippet", ""),
                published_at=published_at,
                raw_date=raw.get("date_str"),
            )
            articles.append(article)
    
    print(f"[Repubblica] Scraped {len(articles)} articles from {len(SECTIONS)} sections")
    return articles
