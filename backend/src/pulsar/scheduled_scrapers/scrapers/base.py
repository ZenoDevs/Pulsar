"""Base configuration and utilities for scheduled scrapers."""

import hashlib
import time
import random
from typing import List

import requests
from bs4 import BeautifulSoup

from ...domain import Article
from ...infrastructure.scrapers.news_scrapers import (
    scrape_full_text,
    SOURCE_BIAS,
    SOURCE_NAMES,
)


# Common HTTP headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}


def generate_article_id(source_id: str, title: str) -> str:
    """Generate a deterministic ID based on source and title."""
    raw = f"{source_id}:{title}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def fetch_page(url: str, delay: tuple = (0.3, 0.8)) -> BeautifulSoup | None:
    """Fetch a page and return BeautifulSoup object."""
    try:
        time.sleep(random.uniform(*delay))
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None


def create_article(
    source_id: str,
    title: str,
    url: str,
    snippet: str = "",
    published_at=None,
    raw_date: str = None,
) -> Article:
    """Create an Article object with common fields."""
    return Article(
        id=generate_article_id(source_id, title),
        source_id=source_id,
        source_name=SOURCE_NAMES.get(source_id, source_id),
        bias=SOURCE_BIAS.get(source_id, "center"),
        bias_source=SOURCE_BIAS.get(source_id, "center"),
        title=title,
        snippet=snippet,
        url=url,
        published_at=published_at,
        raw_date=raw_date,
    )
