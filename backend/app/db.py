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
            embedding TEXT,
            last_updated TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_cached_analysis(url: str):
    conn = get_db_connection()
    cursor = conn.execute('SELECT bias, embedding FROM article_analysis WHERE url = ?', (url,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "bias": row["bias"],
            "embedding": json.loads(row["embedding"]) if row["embedding"] else None
        }
    return None

def cache_analysis(url: str, bias: str, embedding: list):
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO article_analysis (url, bias, embedding, last_updated)
        VALUES (?, ?, ?, ?)
    ''', (url, bias, json.dumps(embedding) if embedding else None, datetime.now()))
    conn.commit()
    conn.close()

# Initialize DB on module load
init_db()
