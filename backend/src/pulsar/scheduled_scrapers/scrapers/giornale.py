"""Il Giornale scraper for scheduled article collection."""

from typing import List

from .base import fetch_page, create_article, Article


# All Il Giornale sections to scrape
SECTIONS = [
    "https://www.ilgiornale.it/sezioni/interni.html",
    "https://www.ilgiornale.it/sezioni/cronache.html",
    "https://www.ilgiornale.it/sezioni/esteri.html",
    "https://www.ilgiornale.it/sezioni/politica.html",
    "https://www.ilgiornale.it/sezioni/economia.html",
]

# Pages per section
MAX_PAGES = 3

SOURCE_ID = "il_giornale"


def _scrape_page(url: str) -> List[dict]:
    """Scrape a single Il Giornale page."""
    articles = []
    
    soup = fetch_page(url)
    if not soup:
        return articles
    
    # Il Giornale uses card-based layout with class card__title
    title_links = soup.find_all("a", class_="card__title")
    
    # Fallback: find h2/h3 with links
    if not title_links:
        headers = soup.find_all(["h2", "h3"])
        for h in headers:
            a = h.find("a")
            if a and a.get("href"):
                title_links.append(a)
    
    for a_tag in title_links:
        try:
            title = a_tag.get_text(strip=True)
            link = a_tag.get("href", "")
            
            if not title or not link or len(title) < 10:
                continue
            
            # Normalize URL
            if link.startswith("/"):
                link = "https://www.ilgiornale.it" + link
            
            if not link.startswith("http"):
                continue
            
            # Find parent card container for snippet and date
            snippet = ""
            date_str = None
            
            parent = a_tag.parent
            # Navigate up to find the card container
            for _ in range(5):
                if parent is None:
                    break
                if parent.name in ["article", "div"] and parent.get("class"):
                    classes = parent.get("class", [])
                    if any("card" in c for c in classes):
                        break
                parent = parent.parent
            
            if parent:
                # Find snippet - Il Giornale uses p.card__abstract
                abstract = parent.find("p", class_="card__abstract")
                if abstract:
                    snippet = abstract.get_text(strip=True)
                
                # Check parent's parent too
                if not snippet and parent.parent:
                    abstract = parent.parent.find("p", class_="card__abstract")
                    if abstract:
                        snippet = abstract.get_text(strip=True)
                
                # Fallback: any p tag with substantial text
                if not snippet:
                    p_tags = parent.find_all("p")
                    for p in p_tags:
                        p_text = p.get_text(strip=True)
                        if len(p_text) > 30:
                            snippet = p_text
                            break
                
                # Find date (card__time)
                time_div = parent.find("div", class_="card__time")
                if time_div:
                    date_str = time_div.get_text(strip=True)
                else:
                    time_tag = parent.find("time")
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
    """Scrape all Il Giornale sections and return Article objects."""
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
                published_at=None,
                raw_date=raw.get("date_str"),
            )
            articles.append(article)
    
    print(f"[Il Giornale] Scraped {len(articles)} articles from {len(SECTIONS)} sections")
    return articles
