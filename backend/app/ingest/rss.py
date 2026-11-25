"""Ingestione dai feed RSS delle testate.

Gli RSS sono molto piu' stabili dello scraping delle pagine di ricerca: sono
la base della prima pagina. Gli scraper di ricerca storici restano per la
ricerca per argomento (``scrapers/news_scrapers.py``).
"""

from __future__ import annotations

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import feedparser
import requests
from bs4 import BeautifulSoup

from ..schemas import Article
from ..sources import SourceInfo, real_sources

log = logging.getLogger("pulsar.rss")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PulsarBot/2.0; +https://github.com/ZenoDevs/Pulsar)",
    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9",
}
TIMEOUT = 12


@dataclass
class FeedHealth:
    source_id: str
    url: str
    ok: bool
    entries: int = 0
    error: Optional[str] = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def article_id(source_id: str, url_or_title: str) -> str:
    return hashlib.md5(f"{source_id}:{url_or_title}".encode("utf-8")).hexdigest()


def _clean_html(html: str) -> str:
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def _entry_date(entry) -> Optional[datetime]:
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime(*t[:6])  # UTC naive
    return None


def _entry_image(e) -> Optional[str]:
    """Immagine dell'articolo dai campi media RSS, dagli enclosure o dal primo <img>."""
    for key in ("media_content", "media_thumbnail"):
        for m in e.get(key) or []:
            url = m.get("url")
            if url and (m.get("medium") in (None, "image") or "image" in (m.get("type") or "image")):
                return url
    for enc in e.get("enclosures") or []:
        if (enc.get("type") or "").startswith("image") and enc.get("href"):
            return enc["href"]
    for html in [e.get("summary", "")] + [c.get("value", "") for c in e.get("content") or []]:
        if html and "<img" in html:
            img = BeautifulSoup(html, "html.parser").find("img")
            if img and img.get("src", "").startswith("http"):
                return img["src"]
    return None


def parse_feed(source: SourceInfo, content: bytes) -> List[Article]:
    parsed = feedparser.parse(content)
    out = []
    for e in parsed.entries:
        title = _clean_html(e.get("title", "")).strip()
        link = e.get("link")
        if not title:
            continue
        summary = _clean_html(e.get("summary", "") or e.get("description", ""))
        content_html = ""
        if e.get("content"):
            content_html = " ".join(c.get("value", "") for c in e["content"])
        body = _clean_html(content_html) if content_html else None
        out.append(
            Article(
                id=article_id(source.id, link or title),
                source_id=source.id,
                source_name=source.name,
                bias=source.leaning,
                bias_source=source.leaning,
                orientation_score=source.orientation,
                title=title,
                snippet=summary[:600],
                body=body if body and len(body) > len(summary) + 200 else None,
                url=link,
                image_url=_entry_image(e),
                published_at=_entry_date(e),
            )
        )
    return out


def fetch_feed(source: SourceInfo, url: str) -> tuple[List[Article], FeedHealth]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        arts = parse_feed(source, r.content)
        return arts, FeedHealth(source.id, url, ok=bool(arts), entries=len(arts), error=None if arts else "feed vuoto")
    except Exception as e:
        return [], FeedHealth(source.id, url, ok=False, error=str(e)[:200])


def fetch_all(
    sources: Optional[List[SourceInfo]] = None,
    max_age_hours: int = 36,
    max_per_source: int = 40,
) -> tuple[List[Article], List[FeedHealth]]:
    sources = sources or real_sources()
    jobs = [(s, u) for s in sources for u in s.feeds]
    articles: Dict[str, Article] = {}
    health: List[FeedHealth] = []
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

    with ThreadPoolExecutor(max_workers=8) as ex:
        for arts, h in ex.map(lambda j: fetch_feed(*j), jobs):
            health.append(h)
            kept = 0
            for a in arts:
                if a.published_at and a.published_at < cutoff:
                    continue
                if kept >= max_per_source:
                    break
                articles.setdefault(a.url or a.id, a)
                kept += 1
    log.info("RSS: %d articoli da %d/%d feed", len(articles), sum(h.ok for h in health), len(health))
    return list(articles.values()), health


def extract_full_text(url: str) -> Optional[str]:
    """Testo completo con trafilatura; ricade sugli estrattori storici."""
    if not url:
        return None
    try:
        import trafilatura

        r = requests.get(url, headers={**HEADERS, "Accept": "text/html"}, timeout=TIMEOUT)
        if r.status_code == 200:
            text = trafilatura.extract(r.text, include_comments=False, include_tables=False, favor_precision=True)
            if text and len(text) > 200:
                return text
    except Exception as e:
        log.debug("trafilatura fallita su %s: %s", url, e)
    try:
        from ..scrapers.news_scrapers import scrape_full_text

        return scrape_full_text(url) or None
    except Exception:
        return None
