"""News scrapers for Italian outlets used by Pulsar.

This module reuses existing scraping logic for ANSA, Il Giornale, and
La Repubblica, and exposes a high-level helper `search_all_sources` that
normalizes results into a common article schema suitable for the API.
"""

import hashlib
import re
from datetime import datetime
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ..schemas import Article
from ..services.openai_service import is_ai_available, enrich_article_smart

SOURCE_BIAS = {
    "ansa": "center",
    "il_giornale": "right",
    "la_repubblica": "left",
}

SOURCE_NAMES = {
    "ansa": "ANSA",
    "il_giornale": "Il Giornale",
    "la_repubblica": "La Repubblica",
}


def _generate_article_id(source_id: str, title: str) -> str:
    """Generate a deterministic ID based on source and title."""
    raw = f"{source_id}:{title}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _enrich_article_with_ai(article: Article) -> Article:
    """
    If AI is available, re-classify the bias based on content.
    This is intended to be run in parallel.
    """
    return enrich_article_smart(article)


def convert_ansa_date(raw_date_str):
    """Convert ANSA raw date strings into datetime objects when possible."""

    try:
        match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4},\s*\d{1,2}:\d{2})", raw_date_str)
        if match:
            date_str = match.group(1)
            return datetime.strptime(date_str, "%d.%m.%Y, %H:%M")
        return None
    except Exception as e:  # pragma: no cover - defensive
        print(f"Errore convert_ansa_date({raw_date_str}): {e}")
        return None


def ansaScraper(regex, max_pages=10, start_date=None, end_date=None):
    ti = []
    te = []
    d = []
    urls = []
    page_number = 0

    try:
        if start_date and end_date:
            delta_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        else:
            delta_days = 9999
    except Exception:
        delta_days = 9999

    if delta_days <= 7:
        period_param = 7
    elif delta_days <= 31:
        period_param = 31
    elif delta_days <= 365:
        period_param = 365
    else:
        period_param = ""

    try:
        while page_number < max_pages * 12:
            url = (
                "https://www.ansa.it/ricerca/ansait/search.shtml"
                f"?start={page_number}"
                f"&tag=&any={regex}"
                "&sezione=&sort=data%3Adesc"
                f"&periodo={period_param}"
            )
            response = requests.get(url)
            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.content, "html.parser")
            titles = soup.find_all("h2", "title")
            texts = soup.find_all("div", "text")
            dates = soup.find_all("p", "meta")

            for title in titles:
                ti.append(title.get_text(strip=True))
                a_tag = title.find("a")
                if a_tag and a_tag.has_attr("href"):
                    link = a_tag["href"]
                    if link.startswith("/"):
                        link = "https://www.ansa.it" + link
                    urls.append(link)
                else:
                    urls.append(None)

            for t in texts:
                te.append(t.get_text(strip=True))

            for meta in dates:
                date_text = meta.get_text(strip=True)
                d.append(date_text)

            page_number += 12

        min_len = min(len(ti), len(te), len(d), len(urls))
        df = pd.DataFrame({
            "Title": ti[:min_len],
            "Text": te[:min_len],
            "Date": d[:min_len],
            "Url": urls[:min_len],
        })

        if not df.empty:
            df["Date"] = df["Date"].apply(convert_ansa_date)

        return df
    except Exception as e:  # pragma: no cover
        print("Ansa scraper error:", e)
        return pd.DataFrame()


def giornaleScraper(regex, max_pages=10, start_date=None, end_date=None):  # noqa: ARG001
    ti = []
    te = []
    d = []
    urls = []
    page_number = 1
    try:
        while page_number <= max_pages:
            current_page = f"https://www.ilgiornale.it/cerca.html?q={regex}&page={page_number}"
            response = requests.get(current_page)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                titles = soup.find_all("a", "card__title")
                texts = soup.find_all("p", "card__abstract")
                dates = soup.find_all("div", "card__time")

                for title in titles:
                    text = BeautifulSoup(str(title), "html.parser").get_text(strip=True)
                    ti.append(text)
                    href = title.get("href")
                    if href and href.startswith("/"):
                        href = "https://www.ilgiornale.it" + href
                    urls.append(href)

                tmp_te = []
                for text in texts:
                    t = BeautifulSoup(str(text), "html.parser").get_text(strip=True)
                    tmp_te.append(t)

                te.extend(tmp_te[: len(titles)])

                for date in dates:
                    dt = BeautifulSoup(str(date), "html.parser").get_text(strip=True)
                    d.append(dt)
            else:
                break

            page_number += 1

        min_len = min(len(ti), len(te), len(d), len(urls))
        df = pd.DataFrame({
            "Title": ti[:min_len],
            "Text": te[:min_len],
            "Date": d[:min_len],
            "Url": urls[:min_len],
        })
        return df
    except Exception as e:  # pragma: no cover
        print("Il Giornale scraper error:", e)
        return pd.DataFrame()


def repubblicaScraper(regex, max_pages=10, start_date=None, end_date=None):
    ti = []
    te = []
    d = []
    urls = []
    page_number = 1

    if start_date:
        from_str = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    else:
        from_str = "1984-01-01"

    if end_date:
        to_str = pd.to_datetime(end_date).strftime("%Y-%m-%d")
    else:
        to_str = "2100-12-31"

    try:
        while page_number <= max_pages:
            url = (
                "https://ricerca.repubblica.it/ricerca/repubblica?"
                f"query={regex}"
                f"&fromdate={from_str}"
                f"&todate={to_str}"
                "&sortby=score&author=&mode=any"
                f"&page={page_number}"
            )
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                articles = soup.find_all("article")

                for article in articles:
                    txt = article.get_text("\n", strip=True)
                    sections = re.split(r"\n\s*\n", txt.strip())
                    sections = [sec.strip() for sec in sections if sec.strip()]
                    if len(sections) >= 2:
                        ti.append(sections[0])
                        te.append(sections[1])
                        time_tag = article.find("time")
                        if time_tag and time_tag.has_attr("datetime"):
                            d.append(time_tag["datetime"])
                        else:
                            d.append("No date found")
                        
                        a_tag = article.find("a")
                        if a_tag and a_tag.has_attr("href"):
                            href = a_tag["href"]
                            # Repubblica search results usually have absolute URLs, but just in case
                            if href.startswith("/"):
                                href = "https://www.repubblica.it" + href
                            urls.append(href)
                        else:
                            urls.append(None)
            else:
                break

            page_number += 1

        min_len = min(len(ti), len(te), len(d), len(urls))
        df = pd.DataFrame({
            "Title": ti[:min_len],
            "Text": te[:min_len],
            "Date": d[:min_len],
            "Url": urls[:min_len],
        })
        return df
    except Exception as e:  # pragma: no cover
        print("La Repubblica scraper error:", e)
        return pd.DataFrame()


def fetch_articles_from_all_sources(
    query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_pages: int = 5,
) -> List[Article]:
    """Run all news scrapers and return a unified list of Article objects."""

    articles: List[Article] = []

    # ANSA
    try:
        df_ansa = ansaScraper(query, max_pages=max_pages, start_date=start_date, end_date=end_date)
        if not df_ansa.empty:
            source_id = "ansa"
            for _, row in df_ansa.iterrows():
                raw_date = None
                parsed_date = None

                if isinstance(row.get("Date"), datetime):
                    parsed_date = row["Date"]
                else:
                    raw_date = str(row.get("Date")) if row.get("Date") is not None else None

                title = str(row.get("Title", ""))
                articles.append(
                    Article(
                        id=_generate_article_id(source_id, title),
                        source_id=source_id,
                        source_name=SOURCE_NAMES[source_id],
                        bias=SOURCE_BIAS[source_id],
                        title=title,
                        snippet=str(row.get("Text", "")),
                        raw_date=raw_date,
                        published_at=parsed_date,
                        url=str(row.get("Url")) if row.get("Url") else None,
                    )
                )
    except Exception as exc:  # pragma: no cover
        print(f"Error while scraping ANSA: {exc}")

    # Il Giornale
    try:
        df_giornale = giornaleScraper(query, max_pages=max_pages, start_date=start_date, end_date=end_date)
        if not df_giornale.empty:
            source_id = "il_giornale"
            for _, row in df_giornale.iterrows():
                raw_date = str(row.get("Date")) if row.get("Date") is not None else None
                title = str(row.get("Title", ""))
                articles.append(
                    Article(
                        id=_generate_article_id(source_id, title),
                        source_id=source_id,
                        source_name=SOURCE_NAMES[source_id],
                        bias=SOURCE_BIAS[source_id],
                        title=title,
                        snippet=str(row.get("Text", "")),
                        raw_date=raw_date,
                        published_at=None,
                        url=str(row.get("Url")) if row.get("Url") else None,
                    )
                )
    except Exception as exc:  # pragma: no cover
        print(f"Error while scraping Il Giornale: {exc}")

    # La Repubblica
    try:
        df_rep = repubblicaScraper(query, max_pages=max_pages, start_date=start_date, end_date=end_date)
        if not df_rep.empty:
            source_id = "la_repubblica"
            for _, row in df_rep.iterrows():
                raw_date = str(row.get("Date")) if row.get("Date") is not None else None
                title = str(row.get("Title", ""))

                parsed_date = None
                try:
                    if raw_date and raw_date != "No date found":
                        parsed_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                except Exception:
                    parsed_date = None

                articles.append(
                    Article(
                        id=_generate_article_id(source_id, title),
                        source_id=source_id,
                        source_name=SOURCE_NAMES[source_id],
                        bias=SOURCE_BIAS[source_id],
                        title=title,
                        snippet=str(row.get("Text", "")),
                        raw_date=raw_date,
                        published_at=parsed_date,
                        url=str(row.get("Url")) if row.get("Url") else None,
                    )
                )
    except Exception as exc:  # pragma: no cover
        print(f"Error while scraping La Repubblica: {exc}")

    # AI Enrichment Step
    # If AI is available, we process articles in parallel to update their bias
    if is_ai_available() and articles:
        print(f"Enriching {len(articles)} articles with AI analysis...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Map returns an iterator, we force it to list to execute
            articles = list(executor.map(_enrich_article_with_ai, articles))

    return articles

