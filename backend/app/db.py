import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "cache.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS article_analysis (
            url TEXT PRIMARY KEY,
            bias TEXT,
            bias_article TEXT,
            bias_confidence REAL,
            bias_explanation TEXT,
            embedding TEXT,
            last_updated TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            url TEXT UNIQUE,
            source_id TEXT,
            title TEXT,
            snippet TEXT,
            body TEXT,
            published_at TIMESTAMP,
            fetched_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_cached_analysis(url: str):
    conn = get_db_connection()
    cursor = conn.execute('SELECT bias, bias_article, bias_confidence, bias_explanation, embedding FROM article_analysis WHERE url = ?', (url,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "bias": row["bias"],
            "bias_article": row["bias_article"],
            "bias_confidence": row["bias_confidence"],
            "bias_explanation": row["bias_explanation"],
            "embedding": json.loads(row["embedding"]) if row["embedding"] else None
        }
    return None

def cache_analysis(url: str, bias: str, embedding: list, bias_article: str = None, bias_confidence: float = None, bias_explanation: str = None):
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO article_analysis (url, bias, bias_article, bias_confidence, bias_explanation, embedding, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (url, bias, bias_article, bias_confidence, bias_explanation, json.dumps(embedding) if embedding else None, datetime.now()))
    conn.commit()
    conn.close()

def get_article_by_url(url: str):
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM articles WHERE url = ?', (url,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_article(article_data: dict):
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO articles (id, url, source_id, title, snippet, body, published_at, fetched_at)
        VALUES (:id, :url, :source_id, :title, :snippet, :body, :published_at, :fetched_at)
    ''', article_data)
    conn.commit()
    conn.close()

def search_articles_in_db(query: str, start_date: str = None, end_date: str = None):
    conn = get_db_connection()
    # Basic text search on title/body
    sql = '''
        SELECT a.*, aa.bias, aa.bias_article, aa.bias_confidence, aa.bias_explanation, aa.embedding 
        FROM articles a
        LEFT JOIN article_analysis aa ON a.url = aa.url
        WHERE (a.title LIKE ? OR a.body LIKE ?)
    '''
    # Add wildcards for LIKE
    wildcard_query = f"%{query}%"
    params = [wildcard_query, wildcard_query]
    
    if start_date:
        sql += ' AND date(a.published_at) >= date(?)'
        params.append(start_date)
    
    if end_date:
        sql += ' AND date(a.published_at) <= date(?)'
        params.append(end_date)
    
    # Order by newest first and limit to avoid performance issues
    sql += ' ORDER BY a.published_at DESC LIMIT 500'
        
    cursor = conn.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        d = dict(row)
        # Parse embedding from JSON string if present
        if d.get("embedding"):
            try:
                d["embedding"] = json.loads(d["embedding"])
            except:
                d["embedding"] = None
        results.append(d)
        
    return results

# Initialize DB on module load
init_db()
