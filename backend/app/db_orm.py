import os
import json
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, JSON, func, or_
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# Legge l'URL dal file .env. Se non c'è, usa SQLite locale come fallback.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cache.db")

# Fix per compatibilità SQLAlchemy con stringhe Postgres (postgres:// -> postgresql://)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

Base = declarative_base()

# --- Models ---

class ArticleModel(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True)
    url = Column(String, unique=True, index=True)
    source_id = Column(String)
    title = Column(String)
    snippet = Column(Text)
    body = Column(Text)
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Analysis fields (merged from old article_analysis table for simplicity in ORM)
    bias = Column(String, nullable=True)
    bias_article = Column(String, nullable=True)
    bias_confidence = Column(Float, nullable=True)
    bias_explanation = Column(Text, nullable=True)
    embedding = Column(JSON, nullable=True) # In Postgres this will be VECTOR type later
    
    # Track which queries found this article
    search_queries = Column(JSON, default=list)

# --- Database Connection ---

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for FastAPI to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Data Access Layer (DAL) ---
# Funzioni helper per mantenere compatibilità col vecchio codice senza riscrivere tutto subito

def get_cached_analysis(url: str):
    """
    Legacy helper: retrieves analysis data.
    Now queries the main ArticleModel since we merged tables conceptually.
    """
    session = SessionLocal()
    try:
        article = session.query(ArticleModel).filter(ArticleModel.url == url).first()
        if article and article.bias:
            return {
                "bias": article.bias,
                "bias_article": article.bias_article,
                "bias_confidence": article.bias_confidence,
                "bias_explanation": article.bias_explanation,
                "embedding": article.embedding
            }
        return None
    finally:
        session.close()

def cache_analysis(url: str, bias: str, embedding: list, bias_article: str = None, bias_confidence: float = None, bias_explanation: str = None):
    """
    Legacy helper: updates an existing article with analysis data.
    """
    session = SessionLocal()
    try:
        article = session.query(ArticleModel).filter(ArticleModel.url == url).first()
        if article:
            article.bias = bias
            article.bias_article = bias_article
            article.bias_confidence = bias_confidence
            article.bias_explanation = bias_explanation
            article.embedding = embedding
            session.commit()
        else:
            # If article doesn't exist yet (rare edge case in current flow), create partial
            # But usually we save article first.
            pass 
    except Exception as e:
        print(f"DB Error caching analysis: {e}")
        session.rollback()
    finally:
        session.close()

def get_article_by_url(url: str):
    session = SessionLocal()
    try:
        article = session.query(ArticleModel).filter(ArticleModel.url == url).first()
        if article:
            # Convert to dict to match old API expectation
            return {
                "id": article.id,
                "url": article.url,
                "source_id": article.source_id,
                "title": article.title,
                "snippet": article.snippet,
                "body": article.body,
                "published_at": article.published_at,
                "fetched_at": article.fetched_at,
                "bias": article.bias
            }
        return None
    finally:
        session.close()

def save_article(article_data: dict, query: str = None):
    session = SessionLocal()
    try:
        # Check if exists
        article = session.query(ArticleModel).filter(ArticleModel.url == article_data["url"]).first()
        
        # Parse date if string
        pub_at = article_data.get("published_at")
        if isinstance(pub_at, str):
            try:
                pub_at = datetime.fromisoformat(pub_at)
            except:
                pub_at = None

        if article:
            # Update fields
            article.title = article_data["title"]
            article.snippet = article_data["snippet"]
            article.body = article_data["body"]
            article.published_at = pub_at
            
            # Update search queries list
            if query:
                current_queries = list(article.search_queries) if article.search_queries else []
                if query not in current_queries:
                    current_queries.append(query)
                    article.search_queries = current_queries
        else:
            # Create new
            initial_queries = [query] if query else []
            article = ArticleModel(
                id=article_data["id"],
                url=article_data["url"],
                source_id=article_data["source_id"],
                title=article_data["title"],
                snippet=article_data["snippet"],
                body=article_data["body"],
                published_at=pub_at,
                fetched_at=datetime.utcnow(),
                search_queries=initial_queries
            )
            session.add(article)
        
        session.commit()
    except Exception as e:
        print(f"DB Error saving article: {e}")
        session.rollback()
    finally:
        session.close()

def search_articles_in_db(query: str, start_date: str = None, end_date: str = None):
    session = SessionLocal()
    try:
        # Search in Title OR Snippet (Smart Search)
        search_filter = or_(
            ArticleModel.title.ilike(f"%{query}%"),
            ArticleModel.snippet.ilike(f"%{query}%")
        )
        
        q = session.query(ArticleModel).filter(search_filter)
        
        if start_date:
            try:
                sd = datetime.fromisoformat(start_date)
                q = q.filter(ArticleModel.published_at >= sd)
            except: pass
            
        if end_date:
            try:
                ed = datetime.fromisoformat(end_date)
                q = q.filter(ArticleModel.published_at <= ed)
            except: pass
            
        # Order by newest
        results = q.order_by(ArticleModel.published_at.desc()).limit(500).all()
        
        # Convert to list of dicts
        out = []
        for r in results:
            out.append({
                "id": r.id,
                "url": r.url,
                "source_id": r.source_id,
                "title": r.title,
                "snippet": r.snippet,
                "body": r.body,
                "published_at": r.published_at,
                "bias": r.bias,
                "bias_article": r.bias_article,
                "bias_confidence": r.bias_confidence,
                "bias_explanation": r.bias_explanation,
                "embedding": r.embedding
            })
        return out
    finally:
        session.close()

def get_latest_article_date(query: str) -> Optional[datetime]:
    session = SessionLocal()
    try:
        search_filter = or_(
            ArticleModel.title.ilike(f"%{query}%"),
            ArticleModel.snippet.ilike(f"%{query}%")
        )
        latest = session.query(func.max(ArticleModel.published_at)).filter(search_filter).scalar()
        return latest
    finally:
        session.close()

# Initialize DB
init_db()
