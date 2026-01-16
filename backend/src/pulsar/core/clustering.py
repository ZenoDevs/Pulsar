import re
import uuid
from collections import Counter
from datetime import datetime
from typing import List, Set, Dict

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from ..domain import Article, Cluster, ClusterStats
from ..infrastructure.clients.openai import (
    is_ai_available, 
    generate_cluster_title,
    check_clusters_merge
)


def _normalize_text(text: str) -> Set[str]:
    """Convert text to a set of lowercase words, removing punctuation and stop words."""
    text = text.lower()
    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text)
    words = text.split()
    # Basic stop words for Italian (very minimal list for MVP)
    # TODO: Expand this list or use a library for better stop word removal
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


def _compute_stats(articles: List[Article]) -> ClusterStats:
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

    return ClusterStats(
        total_articles=total,
        by_bias=final_bias,
        by_source=dict(by_source),
        first_published_at=first_published,
        last_published_at=last_published,
    )


def cluster_articles(query: str, articles: List[Article]) -> List[Cluster]:
    """
    Group articles into stories using Hierarchical Agglomerative Clustering (HAC)
    and AI-powered merging for high precision.
    """
    if not articles:
        return []

    use_ai = is_ai_available()
    clusters: List[List[Article]] = []

    # --- PHASE 1: Initial Clustering (HAC or Jaccard) ---
    
    # Filter articles that have embeddings
    articles_with_emb = [a for a in articles if a.embedding] if use_ai else []
    
    if use_ai and len(articles_with_emb) > 1:
        print(f"Using HAC with {len(articles_with_emb)} articles...")
        try:
            # Prepare Matrix
            X = np.array([a.embedding for a in articles_with_emb])
            
            # HAC Configuration
            # metric='cosine' computes cosine distance (1 - similarity)
            # distance_threshold=0.35 implies similarity threshold of 0.65
            hac = AgglomerativeClustering(
                n_clusters=None,
                metric='cosine',
                linkage='average',
                distance_threshold=0.35
            )
            labels = hac.fit_predict(X)
            
            # Group by labels
            temp_clusters: Dict[int, List[Article]] = {}
            for idx, label in enumerate(labels):
                if label not in temp_clusters:
                    temp_clusters[label] = []
                temp_clusters[label].append(articles_with_emb[idx])
            
            clusters = list(temp_clusters.values())
            
            # Handle articles without embeddings (if any)
            orphans = [a for a in articles if not a.embedding]
            if orphans:
                # Simple fallback: add them as singletons (or could try Jaccard against clusters)
                for o in orphans:
                    clusters.append([o])
                    
        except Exception as e:
            print(f"HAC failed: {e}. Falling back to Jaccard.")
            clusters = _fallback_jaccard_clustering(articles)
    else:
        print("Using Jaccard Similarity (Fallback)...")
        clusters = _fallback_jaccard_clustering(articles)

    # --- PHASE 2: AI Merge (The "Magic Touch") ---
    
    if use_ai and len(clusters) > 1:
        print(f"Checking for merges among {len(clusters)} clusters...")
        
        # Prepare input for AI: ID and Titles
        cluster_previews = []
        for i, cluster in enumerate(clusters):
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

    # --- PHASE 3: Cluster Object Creation ---

    result: List[Cluster] = []

    for cluster_articles in clusters:
        # Sort articles by date (newest first)
        cluster_articles.sort(key=lambda a: a.published_at or datetime.min, reverse=True)

        # Generate AI Title if cluster is significant
        cluster_title = cluster_articles[0].title
        if use_ai and len(cluster_articles) > 1:
             titles = [a.title for a in cluster_articles]
             cluster_title = generate_cluster_title(titles)

        stats = _compute_stats(cluster_articles)
        cluster_id = str(uuid.uuid4())

        result.append(
            Cluster(
                id=cluster_id,
                query=query,
                title=cluster_title,
                articles=cluster_articles,
                stats=stats,
            )
        )

    # Sort clusters by total articles (hotness)
    result.sort(key=lambda c: c.stats.total_articles, reverse=True)

    return result


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

