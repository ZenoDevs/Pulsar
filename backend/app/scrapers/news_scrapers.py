"""News scrapers for Italian outlets used by Pulsar.

This module reuses existing scraping logic for ANSA, Il Giornale, and
La Repubblica, and exposes a high-level helper `search_all_sources` that
normalizes results into a common article schema suitable for the API.
"""

import hashlib
import re
import time
import random
from datetime import datetime
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ..schemas import Article
from ..services.openai_service import is_ai_available, enrich_article_smart
from ..db import get_article_by_url, save_article

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
    Full enrichment pipeline:
    1. Check DB for existing body/analysis.
    2. If missing body, scrape full text.
    3. Save/Update DB.
    4. Run AI analysis (Bias/Embedding) using full context.
    """
    # 1. Check DB for existing body
    if article.url:
        existing = get_article_by_url(article.url)
        if existing and existing.get("body"):
            article.body = existing["body"]
    
    # 2. Scrape if needed (and if we have a URL)
    if not article.body and article.url:
        # print(f"Scraping full text for: {article.title[:30]}...")
        article.body = scrape_full_text(article.url)
        
        # 3. Save to DB
        # Prepare dict for DB
        article_data = {
            "id": article.id,
            "url": article.url,
            "source_id": article.source_id,
            "title": article.title,
            "snippet": article.snippet,
            "body": article.body,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "fetched_at": article.fetched_at.isoformat()
        }
        save_article(article_data)

    # 4. AI Analysis (Bias + Embedding)
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

    # Add headers to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

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
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                articles = soup.find_all("article")

                for article in articles:
                    # 1. Title & Link
                    header = article.find(["h1", "h2"])
                    if not header:
                        continue
                    
                    a_tag = header.find("a")
                    if not a_tag:
                        continue
                        
                    title_text = header.get_text(strip=True)
                    link_url = a_tag.get("href")
                    
                    if link_url and link_url.startswith("/"):
                        link_url = "https://www.repubblica.it" + link_url
                        
                    # 2. Date
                    date_val = "No date found"
                    time_tag = article.find("time")
                    if time_tag and time_tag.has_attr("datetime"):
                        date_val = time_tag["datetime"]
                    else:
                        # Try to find text looking like a date
                        text_content = article.get_text(" ", strip=True)
                        match = re.search(r"(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})", text_content, re.IGNORECASE)
                        if match:
                            date_val = f"{match.group(1)} {match.group(2)} {match.group(3)}"

                    # 3. Snippet
                    snippet_text = ""
                    # Try to find a <p> that is not metadata
                    p_tags = article.find_all("p")
                    for p in p_tags:
                        ptxt = p.get_text(strip=True)
                        if len(ptxt) > 20:
                            snippet_text = ptxt
                            break
                    
                    if not snippet_text:
                        # Fallback: text minus title
                        full_txt = article.get_text(" ", strip=True)
                        snippet_text = full_txt.replace(title_text, "").strip()
                        if len(snippet_text) > 300:
                            snippet_text = snippet_text[:300] + "..."

                    ti.append(title_text)
                    urls.append(link_url)
                    d.append(date_val)
                    te.append(snippet_text)
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
    max_pages: int = 2,
    enrich_with_ai: bool = True,
) -> List[Article]:
    """Run all news scrapers in parallel and return a unified list of Article objects."""

    articles: List[Article] = []

    def scrape_ansa_wrapper():
        results = []
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
                    results.append(
                        Article(
                            id=_generate_article_id(source_id, title),
                            source_id=source_id,
                            source_name=SOURCE_NAMES[source_id],
                            bias=SOURCE_BIAS[source_id],
                            bias_source=SOURCE_BIAS[source_id],
                            title=title,
                            snippet=str(row.get("Text", "")),
                            raw_date=raw_date,
                            published_at=parsed_date,
                            url=str(row.get("Url")) if row.get("Url") else None,
                        )
                    )
        except Exception as exc:
            print(f"Error while scraping ANSA: {exc}")
        return results

    def scrape_giornale_wrapper():
        results = []
        try:
            df_giornale = giornaleScraper(query, max_pages=max_pages, start_date=start_date, end_date=end_date)
            if not df_giornale.empty:
                source_id = "il_giornale"
                for _, row in df_giornale.iterrows():
                    raw_date = str(row.get("Date")) if row.get("Date") is not None else None
                    title = str(row.get("Title", ""))
                    results.append(
                        Article(
                            id=_generate_article_id(source_id, title),
                            source_id=source_id,
                            source_name=SOURCE_NAMES[source_id],
                            bias=SOURCE_BIAS[source_id],
                            bias_source=SOURCE_BIAS[source_id],
                            title=title,
                            snippet=str(row.get("Text", "")),
                            raw_date=raw_date,
                            published_at=None,
                            url=str(row.get("Url")) if row.get("Url") else None,
                        )
                    )
        except Exception as exc:
            print(f"Error while scraping Il Giornale: {exc}")
        return results

    def scrape_repubblica_wrapper():
        results = []
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

                    results.append(
                        Article(
                            id=_generate_article_id(source_id, title),
                            source_id=source_id,
                            source_name=SOURCE_NAMES[source_id],
                            bias=SOURCE_BIAS[source_id],
                            bias_source=SOURCE_BIAS[source_id],
                            title=title,
                            snippet=str(row.get("Text", "")),
                            raw_date=raw_date,
                            published_at=parsed_date,
                            url=str(row.get("Url")) if row.get("Url") else None,
                        )
                    )
        except Exception as exc:
            print(f"Error while scraping La Repubblica: {exc}")
        return results

    # Run scrapers in parallel
    print("Starting parallel scraping...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_ansa = executor.submit(scrape_ansa_wrapper)
        future_giornale = executor.submit(scrape_giornale_wrapper)
        future_repubblica = executor.submit(scrape_repubblica_wrapper)
        
        articles.extend(future_ansa.result())
        articles.extend(future_giornale.result())
        articles.extend(future_repubblica.result())
    
    print(f"Scraping finished. Found {len(articles)} articles.")

    # AI Enrichment Step
    # If AI is available, we process articles in parallel to update their bias
    if enrich_with_ai and is_ai_available() and articles:
        print(f"Enriching {len(articles)} articles with AI analysis...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Map returns an iterator, we force it to list to execute
            articles = list(executor.map(_enrich_article_with_ai, articles))

    return articles


def scrape_full_text(url: str) -> str:
    """
    Visits the article URL and extracts the full body text.
    Includes specific heuristics for supported sources.
    """
    if not url:
        return ""
        
    try:
        # Be polite and avoid getting blocked
        time.sleep(random.uniform(0.5, 1.5))
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.content, "html.parser")
        text = ""

        # Heuristics based on source domain
        if "ansa.it" in url:
            # ANSA usually puts text in div.news-txt
            container = soup.find("div", class_="news-txt") or soup.find("div", class_="story-text")
            if container:
                text = container.get_text(separator="\n", strip=True)
        
        elif "ilgiornale.it" in url:
            # Il Giornale usually uses div.article-body
            container = soup.find("div", class_="article-body") or soup.find("div", class_="content")
            if container:
                text = container.get_text(separator="\n", strip=True)
                
                # Aggressive cleaning for the IE banner
                # The banner text observed: "Stai utilizzando Internet Eplorer... gratuitamente."
                # We look for the specific end marker "gratuitamente."
                if "Internet Eplorer" in text or "Internet Explorer" in text:
                    marker = "gratuitamente."
                    idx = text.find(marker)
                    if idx != -1:
                        # Cut everything up to the end of the marker
                        text = text[idx + len(marker):].strip()
                    else:
                        # Fallback: if we see the warning but not the exact marker, 
                        # try to find the end of the sentence by looking for the first newline 
                        # after the warning start, or just cut a fixed length.
                        # The banner is usually around 200-300 chars.
                        if len(text) > 300:
                            text = text[300:].strip()

        elif "repubblica.it" in url:
            # Repubblica uses div.story__text for articles
            # For videos, we try multiple specific containers
            container = (
                soup.find("div", class_="story__text") or 
                soup.find("div", id="article-body") or
                soup.find("div", class_="story-text") or
                soup.find("p", class_="video-description") or 
                soup.find("div", class_="amp-video-description") or
                soup.find("span", class_="video-caption") or 
                soup.find("div", class_="video-content") or
                soup.find("p", class_="caption") or
                soup.find("p", class_="intro")
            )
            
            if container:
                text = container.get_text(separator="\n", strip=True)
            else:
                # Fallback: Look for the first substantial paragraph inside <main> or <article>
                main_tag = soup.find("main") or soup.find("article")
                if main_tag:
                    paragraphs = main_tag.find_all("p")
                    # Join paragraphs that look like content (len > 30)
                    valid_p = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]
                    if valid_p:
                        text = "\n".join(valid_p)

            # Fallback for videos or paywalled content: use meta description
            if not text or len(text) < 50:
                meta_desc = (
                    soup.find("meta", property="og:description") or 
                    soup.find("meta", attrs={"name": "description"}) or
                    soup.find("meta", property="twitter:description")
                )
                if meta_desc:
                    text = meta_desc.get("content", "").strip()
            
            # Last resort fallback: Title
            if not text:
                if soup.title:
                    text = f"Video content: {soup.title.get_text(strip=True)}"

            # Check for Paywall/Login message (Quotidiano / Edicola)
            paywall_markers = [
                "Naviga veloce e senza interruzioni",
                "Metti in pausa la pubblicità",
                "Abbonati a Repubblica",
                "contenuto riservato agli abbonati"
            ]
            if any(marker in text for marker in paywall_markers):
                print(f"DEBUG: Paywall detected for {url}")
                return ""

        # Generic fallback: grab all substantial paragraphs
        if not text:
            paragraphs = soup.find_all("p")
            # Filter out short snippets/captions
            valid_p = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50]
            text = "\n\n".join(valid_p)

        # --- GLOBAL CLEANING RULES ---
        # Apply these rules regardless of how the text was extracted
        
        # 1. Il Giornale "Internet Explorer" Banner
        if "ilgiornale.it" in url:
            # Check for the banner start
            start_idx = text.find("Internet Eplorer")
            if start_idx == -1:
                start_idx = text.find("Internet Explorer")
            
            if start_idx != -1:
                print(f"DEBUG: Banner found in {url}")
                # Look for the end marker "gratuitamente" after the start
                end_marker = "gratuitamente"
                end_idx = text.find(end_marker, start_idx)
                
                if end_idx != -1:
                    # Cut everything up to the end of "gratuitamente"
                    # + 1 for the dot if it exists, but lstrip will handle it
                    raw_cut = text[end_idx + len(end_marker):]
                    # Clean leading punctuation and whitespace
                    text = raw_cut.lstrip(" .:\n\t")
                else:
                    # Fallback: if we see the warning but not the end marker
                    if len(text) > 300:
                        text = text[300:].strip()

        return text

    except Exception as e:
        print(f"Error scraping full text for {url}: {e}")
        return ""

