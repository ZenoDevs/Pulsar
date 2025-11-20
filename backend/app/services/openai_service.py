import os
import json
from typing import List, Optional
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
# Switch to ORM implementation
from ..db_orm import get_cached_analysis, cache_analysis
from sqlalchemy.orm import Session

# Load environment variables from .env file
load_dotenv()

client = None
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    client = OpenAI(api_key=api_key)

def is_ai_available() -> bool:
    """Check if OpenAI API key is configured."""
    return client is not None

def enrich_article_smart(article, db: Session):
    """
    Enrich article with Bias and Embedding, using Cache if available.
    Modifies the article object in place.
    """
    if not is_ai_available():
        return article

    # Check Cache
    cached = get_cached_analysis(db, article.url)
    if cached:
        article.bias = cached["bias"]
        article.bias_article = cached.get("bias_article")
        article.bias_confidence = cached.get("bias_confidence")
        article.bias_explanation = cached.get("bias_explanation")
        article.embedding = cached["embedding"]
        return article

    # Not in cache, compute
    # 1. Bias
    # Use body if available, otherwise snippet
    text_content = article.snippet or ""
    
    # Call AI classification
    ai_result = classify_bias(article.title, text_content, article.source_name, article.body)
    
    # Store AI results
    article.bias_article = ai_result["bias"]
    article.bias_confidence = ai_result["confidence"]
    article.bias_explanation = ai_result["explanation"]
    
    # Fusion Logic (Layer 2)
    # If confidence is low, fallback to source bias.
    # If source bias is missing (shouldn't happen), use AI bias.
    threshold = 0.65
    
    if article.bias_confidence < threshold and article.bias_source:
        article.bias = article.bias_source
    else:
        article.bias = article.bias_article

    # 2. Embedding (combine title + snippet + part of body)
    body_part = article.body[:1000] if article.body else ""
    text_to_embed = f"{article.title} {text_content} {body_part}"
    embedding = get_embedding(text_to_embed)
    article.embedding = embedding

    # Save to Cache
    if article.url:
        # Use the effective bias we just calculated
        cache_analysis(
            db,
            article.url, 
            article.bias, 
            embedding,
            bias_article=article.bias_article,
            bias_confidence=article.bias_confidence,
            bias_explanation=article.bias_explanation
        )
    
    return article

def get_embedding(text: str) -> Optional[List[float]]:
    """
    Get the embedding vector for a given text using OpenAI's text-embedding-3-small.
    Returns None if the client is not configured or an error occurs.
    """
    if not client:
        return None
    
    try:
        # Clean text
        text = text.replace("\n", " ")
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error fetching embedding: {e}")
        return None

def classify_bias(title: str, snippet: str, source_name: str, body: str = None) -> dict:
    """
    Analyze the bias of an article using GPT-4o-mini.
    Returns a dict with: 'bias', 'confidence', 'explanation'.
    """
    default_result = {"bias": "unknown", "confidence": 0.0, "explanation": "Analysis failed"}
    
    if not client:
        return default_result

    # Use body if available (truncated), otherwise snippet
    context_text = body[:2500] if body else snippet

    prompt = f"""
    You are an expert media analyst. Analyze the political bias of the following news article from the Italian press.
    
    Source: {source_name}
    Title: {title}
    Content: {context_text}

    Determine if the tone and framing are leaning Left, Right, or are Neutral/Center.
    Consider the typical stance of the source but prioritize the specific content provided.

    CRITICAL - Confidence Scoring Rules:
    - < 0.6: If the text is very short, purely factual (cronaca), or ambiguous.
    - 0.6 - 0.8: If there is some framing or selective emphasis but no strong opinion.
    - > 0.8: If there is explicit opinion, strong adjectives, or clear political agenda.
    
    Return ONLY a JSON object with this format:
    {{
        "bias": "left" | "center" | "right" | "unknown",
        "confidence": float (0.0 to 1.0),
        "explanation": "short natural language explanation in Italian (max 20 words)"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        return {
            "bias": data.get("bias", "unknown"),
            "confidence": data.get("confidence", 0.0),
            "explanation": data.get("explanation", "")
        }
    except Exception as e:
        print(f"Error classifying bias: {e}")
        return default_result

def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec1 or not vec2:
        return 0.0
    
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
        
    return float(np.dot(v1, v2) / (norm1 * norm2))

def generate_story_title(titles: List[str]) -> str:
    """
    Generate a representative title for a cluster of articles.
    """
    if not client or not titles:
        return titles[0] if titles else "Nuova Storia"

    # Limit to first 10 titles to save tokens, usually enough to get the gist
    titles_text = "\n".join(f"- {t}" for t in titles[:10])
    
    prompt = f"""
    You are a news editor. Create a short, neutral, and descriptive headline (in Italian) that summarizes the following group of article titles about the same event.
    
    Titles:
    {titles_text}
    
    The headline must be objective and cover the main event. Max 15 words. Do not use quotes.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful news editor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=60
        )
        return response.choices[0].message.content.strip().replace('"', '')
    except Exception as e:
        print(f"Error generating title: {e}")
        return titles[0]

def check_clusters_merge(clusters_data: List[dict]) -> List[List[int]]:
    """
    Ask AI if any of the provided story clusters refer to the same event.
    Input: [{'id': 0, 'titles': ['Title 1', 'Title 2']}, {'id': 1, 'titles': ['Title A']}]
    Output: [[0, 3], [2, 5]] (list of groups of IDs to merge)
    """
    if not client or len(clusters_data) < 2:
        return []

    # Format input for AI: ID and a few titles to give context
    clusters_text = ""
    for c in clusters_data:
        # Take top 3 titles to give better context
        t_list = " || ".join(c['titles'][:3]) 
        clusters_text += f"Cluster ID {c['id']}: {t_list}\n"
    
    prompt = f"""
    You are a Chief Editor for a news aggregator. I have a list of story clusters, each represented by a few headlines from different sources.
    
    Your goal is to identify clusters that refer to the **SAME EVENT** or **SAME TOPIC** and should be merged.
    
    Rules for merging:
    1. Merge if they cover the exact same specific event (e.g. "Protest in Rome" and "Rome demonstration for Gaza").
    2. Merge if one is a sub-story of the other happening on the same day (e.g. "Mattarella meets Abu Mazen" and "Mattarella's speech at Quirinale").
    3. Do NOT merge if they are distinct separate events (e.g. "Protest in Milan" vs "Protest in Rome" - unless explicitly stated as part of a national strike).
    
    Clusters:
    {clusters_text}
    
    Return a JSON object with a key "merges" containing a list of lists. Each inner list contains the IDs that should be merged.
    Example: {{ "merges": [[1, 4], [2, 5, 8]] }}
    If no merges are needed, return {{ "merges": [] }}.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        return data.get("merges", [])
    except Exception as e:
        print(f"Error checking merges: {e}")
        return []

def analyze_story_coverage(articles: List) -> str:
    """
    Generate a comprehensive analysis of the story coverage.
    Includes:
    1. Why certain sources might be biased (citing specific articles).
    2. A neutral overview of the event.
    """
    if not client or not articles:
        return "Analisi non disponibile."

    # Prepare input for AI
    articles_text = ""
    for i, a in enumerate(articles[:15]): # Limit to 15 articles to save context
        # Use body if available (truncated to ~300 chars) to give more substance to the analysis
        content_preview = (a.body[:300] + "...") if a.body else a.snippet
        content_preview = content_preview.replace("\n", " ").strip()
        
        articles_text += f"[{i+1}] Source: {a.source_name} ({a.bias})\n   Title: {a.title}\n   Excerpt: {content_preview}\n\n"

    prompt = f"""
    You are an expert media analyst and neutral observer. Analyze the following set of news articles covering the same event.
    
    Articles:
    {articles_text}
    
    Please provide a response in Italian with two distinct sections:
    
    1. **Analisi della Copertura**: Explain how different sources are framing the event. Be CONCISE and DIRECT. Avoid generic introductions. Focus immediately on the differences in tone and framing.
       IMPORTANT: When citing a specific angle or claim, refer to the article by its **FULL TITLE** in italics.
       Example: "Nell'articolo *"Titolo Completo Dell'Articolo"*, si punta il dito contro..." or "Come riportato in *"Altro Titolo"*, il tono è...".
    
    2. **Panoramica Neutrale**: Provide a purely factual, neutral summary of the event based on the common facts across all sources. Ensure this section is complete and not cut off.
    
    Keep the tone professional, objective, and insightful. Use Markdown formatting.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful media analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating analysis: {e}")
        return "Errore durante la generazione dell'analisi."
