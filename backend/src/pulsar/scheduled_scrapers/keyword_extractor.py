"""Keyword extraction using GPT-4o-mini.

Extracts 4-5 relevant keywords from article content for search indexing.
"""

import os
import json
from typing import List, Optional

from openai import OpenAI
from dotenv import load_dotenv

from ..core.config import settings

load_dotenv()

# Initialize OpenAI client
_client: Optional[OpenAI] = None
_api_key = os.getenv("OPENAI_API_KEY")

if settings.ai.enabled and _api_key:
    _client = OpenAI(api_key=_api_key)


def is_extractor_available() -> bool:
    """Check if keyword extraction is available (OpenAI configured)."""
    return _client is not None


def extract_keywords(title: str, body: str = "", snippet: str = "") -> List[str]:
    """
    Extract 4-5 relevant keywords from an article using GPT-4o-mini.
    
    Args:
        title: Article title
        body: Full article body text (optional)
        snippet: Article snippet/summary (optional, used if body not available)
    
    Returns:
        List of 4-5 keywords as strings
    """
    if not _client:
        print("[Keyword Extractor] OpenAI client not available, skipping extraction")
        return []
    
    # Build context from available content
    content = title
    if body:
        # Use first 2000 chars of body to save tokens
        content += f"\n\n{body[:2000]}"
    elif snippet:
        content += f"\n\n{snippet}"
    
    if not content.strip():
        return []
    
    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Sei un esperto di analisi di notizie italiane. Il tuo compito è estrarre le parole chiave più rilevanti da un articolo di giornale.

Regole:
- Estrai esattamente 4-5 parole chiave
- Le keywords devono essere in italiano
- Preferisci nomi propri (persone, luoghi, organizzazioni) e concetti chiave
- Evita parole troppo generiche (es: "Italia", "governo" da sole)
- Ogni keyword può essere composta da 1-3 parole
- Restituisci SOLO un array JSON di stringhe, senza altro testo

Esempio output: ["Giorgia Meloni", "riforma pensioni", "Bruxelles", "sindacati", "manovra economica"]"""
                },
                {
                    "role": "user",
                    "content": f"Estrai le keywords da questo articolo:\n\n{content}"
                }
            ],
            temperature=0.3,
            max_tokens=150,
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        # Handle potential markdown code blocks
        if result_text.startswith("```"):
            # Remove markdown code block
            lines = result_text.split("\n")
            result_text = "\n".join(lines[1:-1])
        
        keywords = json.loads(result_text)
        
        if isinstance(keywords, list):
            # Ensure all items are strings and limit to 5
            keywords = [str(k).strip() for k in keywords if k][:5]
            return keywords
        
        return []
        
    except json.JSONDecodeError as e:
        print(f"[Keyword Extractor] Failed to parse JSON response: {e}")
        return []
    except Exception as e:
        print(f"[Keyword Extractor] Error extracting keywords: {e}")
        return []


def extract_keywords_batch(articles: List[dict]) -> dict:
    """
    Extract keywords for multiple articles.
    
    Args:
        articles: List of dicts with 'url', 'title', 'body', 'snippet' keys
    
    Returns:
        Dict mapping URL to list of keywords
    """
    results = {}
    
    for article in articles:
        url = article.get("url", "")
        if not url:
            continue
        
        keywords = extract_keywords(
            title=article.get("title", ""),
            body=article.get("body", ""),
            snippet=article.get("snippet", ""),
        )
        results[url] = keywords
    
    return results
