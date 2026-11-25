import os
import re
import uuid
from collections import Counter
from datetime import datetime
from typing import List, Set, Dict

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from .schemas import Article, Story, StoryStats
from .services.openai_service import (
    is_ai_available, 
    compute_cosine_similarity, 
    generate_story_title,
    check_clusters_merge
)


ITALIAN_STOPWORDS = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a", "da",
    "in", "con", "su", "per", "tra", "fra", "e", "o", "ma", "se", "che",
    "non", "ha", "ho", "è", "sono", "del", "della", "dei", "delle", "al",
    "allo", "alla", "ai", "agli", "alle", "dal", "dallo", "dalla", "dai",
    "dagli", "dalle", "nel", "nello", "nella", "nei", "negli", "nelle",
    "sul", "sullo", "sulla", "sui", "sugli", "sulle", "come", "piu", "anche",
    "dopo", "ed", "si", "ci", "ne", "questo", "questa", "quello", "quella",
    "essere", "stato", "stata", "sara", "suo", "sua", "loro", "cosa", "oggi",
}


def _normalize_text(text: str) -> Set[str]:
    """Convert text to a set of lowercase words, removing punctuation."""
    text = text.lower()
    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text)
    words = text.split()
    # Basic stop words for Italian (very minimal list for MVP)
    stopwords = {
        "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a", "da",
        "in", "con", "su", "per", "tra", "fra", "e", "o", "ma", "se", "che",
        "non", "ha", "ho", "è", "sono", "del", "della", "dei", "delle", "al",
        "allo", "alla", "ai", "agli", "alle", "dal", "dallo", "dalla", "dai",
        "dagli", "dalle", "nel", "nello", "nella", "nei", "negli", "nelle",
        "sul", "sullo", "sulla", "sui", "sugli", "sulle"
    }
    return {w for w in words if w not in stopwords}


def _jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union


def _compute_stats(articles: List[Article]) -> StoryStats:
    total = len(articles)
    by_bias = Counter(a.bias for a in articles)
    by_source = Counter(a.source_id for a in articles)

    # Filter out None dates
    dates = [a.published_at for a in articles if a.published_at]
    first_published = min(dates) if dates else None
    last_published = max(dates) if dates else None

    # Ensure all bias keys exist for cleaner frontend handling
    final_bias = {"left": 0, "center": 0, "right": 0, "unknown": 0}
    final_bias.update(by_bias)

    return StoryStats(
        total_articles=total,
        by_bias=final_bias,
        by_source=dict(by_source),
        first_published_at=first_published,
        last_published_at=last_published,
    )


def cluster_articles_into_stories(query: str, articles: List[Article]) -> List[Story]:
    """
    Group articles into stories using Hierarchical Agglomerative Clustering (HAC)
    and AI-powered merging for high precision.
    """
    if not articles:
        return []

    use_ai = is_ai_available()
    clusters: List[List[Article]] = []

    # --- PHASE 1: Initial Clustering (HAC or Jaccard) ---
    
    articles_with_emb = [a for a in articles if a.embedding]

    if len(articles_with_emb) > 1 and len(articles_with_emb) >= 0.8 * len(articles):
        try:
            clusters = _hac(np.array([a.embedding for a in articles_with_emb]), articles_with_emb, 0.35)
            clusters += [[a] for a in articles if not a.embedding]
        except Exception as e:
            print(f"HAC su embedding fallito: {e}. Uso TF-IDF.")
            clusters = _tfidf_clustering(articles)
    elif len(articles) > 1:
        clusters = _tfidf_clustering(articles)
    else:
        clusters = [articles]

    # --- PHASE 2: AI Merge (The "Magic Touch") ---
    
    if use_ai and len(clusters) > 1:
        print(f"Checking for merges among {len(clusters)} clusters...")
        
        # Prepare input for AI: ID and Titles
        cluster_previews = []
        # Solo i cluster piu' grandi: con centinaia di singoletti il prompt esploderebbe.
        candidates = set(sorted(range(len(clusters)), key=lambda i: -len(clusters[i]))[:60])
        for i, cluster in enumerate(clusters):
            if i not in candidates:
                continue
            # Get top 3 titles from the cluster to give AI better context
            titles = [a.title for a in cluster[:3]]
            cluster_previews.append({
                "id": i,
                "titles": titles
            })
            
        # Ask AI which clusters are the same
        merges = check_clusters_merge(cluster_previews)
        
        if merges:
            print(f"AI suggested merges: {merges}")
            # Apply merges
            # We use a mapping to redirect old cluster indices to new ones
            # Default: map to self
            merge_map = {i: i for i in range(len(clusters))}
            
            for group in merges:
                # group is like [1, 4, 7]
                # We merge everything into the first one (1)
                target = group[0]
                for other in group[1:]:
                    if other in merge_map: # Safety check
                        merge_map[other] = target
            
            # Rebuild clusters
            new_clusters_map: Dict[int, List[Article]] = {}
            for old_id, cluster_articles in enumerate(clusters):
                target_id = merge_map[old_id]
                # If target was also merged into something else (chaining), we should resolve it.
                # But for now, assuming 1-level depth from AI response is enough.
                # To be safe, let's resolve the root.
                while target_id != merge_map[target_id]:
                    target_id = merge_map[target_id]
                
                if target_id not in new_clusters_map:
                    new_clusters_map[target_id] = []
                new_clusters_map[target_id].extend(cluster_articles)
            
            clusters = list(new_clusters_map.values())

    # --- PHASE 3: Story Object Creation ---

    stories: List[Story] = []

    for cluster in clusters:
        # Sort articles by date (newest first)
        cluster.sort(key=lambda a: a.published_at or datetime.min, reverse=True)

        # Generate AI Title if cluster is significant
        story_title = cluster[0].title
        if use_ai and len(cluster) > 1:
             titles = [a.title for a in cluster]
             story_title = generate_story_title(titles)

        stats = _compute_stats(cluster)
        story_id = str(uuid.uuid4())

        stories.append(
            Story(
                id=story_id,
                query=query,
                title=story_title,
                articles=cluster,
                stats=stats,
            )
        )

    # Sort stories by total articles (hotness)
    stories.sort(key=lambda s: s.stats.total_articles, reverse=True)

    return stories


def _hac(X, items, threshold: float) -> List[List[Article]]:
    hac = AgglomerativeClustering(
        n_clusters=None, metric="cosine", linkage="average", distance_threshold=threshold
    )
    labels = hac.fit_predict(X)
    groups: Dict[int, List[Article]] = {}
    for item, label in zip(items, labels):
        groups.setdefault(int(label), []).append(item)
    return list(groups.values())


def _tfidf_clustering(articles: List[Article]) -> List[List[Article]]:
    """Clustering senza embedding: TF-IDF su titolo + attacco del testo.

    Meno preciso degli embedding ma gratuito e deterministico: e' il default
    quando non c'e' una chiave OpenAI.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    docs = [f"{a.title} {a.title} {a.snippet} {(a.body or '')[:600]}" for a in articles]
    try:
        vec = TfidfVectorizer(
            lowercase=True, stop_words=list(ITALIAN_STOPWORDS), ngram_range=(1, 1),
            min_df=1, sublinear_tf=True, strip_accents="unicode",
        )
        X = vec.fit_transform(docs).toarray()
        if X.shape[1] == 0:
            raise ValueError("vocabolario vuoto")
        threshold = float(os.getenv("PULSAR_TFIDF_THRESHOLD", "0.88"))
        return _hac(X, articles, threshold)
    except Exception as e:
        print(f"TF-IDF fallito: {e}. Uso Jaccard.")
        return _fallback_jaccard_clustering(articles)


def _fallback_jaccard_clustering(articles: List[Article]) -> List[List[Article]]:
    """Original greedy clustering logic as fallback."""
    clusters: List[List[Article]] = []
    JACCARD_THRESHOLD = 0.25

    for article in articles:
        added = False
        article_tokens = _normalize_text(article.title)

        for cluster in clusters:
            seed_tokens = _normalize_text(cluster[0].title)
            sim = _jaccard_similarity(article_tokens, seed_tokens)
            if sim >= JACCARD_THRESHOLD:
                cluster.append(article)
                added = True
                break
        
        if not added:
            clusters.append([article])
            
    return clusters

