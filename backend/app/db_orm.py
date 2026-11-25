import os
import json
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, JSON, func, or_, Integer, ForeignKey, Table, Boolean, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
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

# Association Table for Many-to-Many relationship between Articles and SearchQueries
article_search_query_association = Table(
    'article_search_query', Base.metadata,
    Column('article_id', String, ForeignKey('articles.id')),
    Column('search_query_id', Integer, ForeignKey('search_queries.id'))
)

class SearchQuery(Base):
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, unique=True, index=True)
    count = Column(Integer, default=1)
    last_searched_at = Column(DateTime, default=datetime.utcnow)
    
    articles = relationship("ArticleModel", secondary=article_search_query_association, back_populates="queries")

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
    orientation_score = Column(Float, nullable=True)
    embedding = Column(JSON, nullable=True) # In Postgres this will be VECTOR type later
    
    # Legacy JSON column (kept for backward compatibility during migration, but we will stop writing to it eventually)
    search_queries = Column(JSON, default=list)
    
    # New Relationship
    queries = relationship("SearchQuery", secondary=article_search_query_association, back_populates="articles")

class StoryRecord(Base):
    """Storia serializzata (articoli + metriche + dossier) per sopravvivere ai riavvii."""
    __tablename__ = "stories"

    id = Column(String, primary_key=True)
    edition_id = Column(String, index=True, nullable=True)
    query = Column(String, nullable=True, index=True)
    title = Column(Text)
    score = Column(Float, default=0.0)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class EditionRecord(Base):
    __tablename__ = "editions"

    id = Column(String, primary_key=True)
    demo = Column(Boolean, default=False)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# --- Database Connection ---

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Crea le tabelle e applica le piccole migrazioni additive."""
    Base.metadata.create_all(bind=engine)
    try:
        cols = {c["name"] for c in inspect(engine).get_columns("articles")}
        if "orientation_score" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE articles ADD COLUMN orientation_score FLOAT"))
    except Exception as e:  # pragma: no cover
        print(f"Migrazione articles.orientation_score non applicata: {e}")

def get_db():
    """Dependency for FastAPI to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Data Access Layer (DAL) ---
# Refactored to accept db session explicitly

def get_cached_analysis(db: Session, url: str):
    """
    Retrieves analysis data using the provided session.
    """
    article = db.query(ArticleModel).filter(ArticleModel.url == url).first()
    if article and article.bias:
        return {
            "bias": article.bias,
            "bias_article": article.bias_article,
            "bias_confidence": article.bias_confidence,
            "bias_explanation": article.bias_explanation,
            "orientation_score": article.orientation_score,
            "embedding": article.embedding
        }
    return None

def cache_analysis(db: Session, url: str, bias: str, embedding: list, bias_article: str = None, bias_confidence: float = None, bias_explanation: str = None, orientation_score: float = None):
    """
    Updates an existing article with analysis data using the provided session.
    """
    try:
        article = db.query(ArticleModel).filter(ArticleModel.url == url).first()
        if article:
            article.bias = bias
            article.bias_article = bias_article
            article.bias_confidence = bias_confidence
            article.bias_explanation = bias_explanation
            article.orientation_score = orientation_score
            article.embedding = embedding
            db.commit()
    except Exception as e:
        print(f"DB Error caching analysis: {e}")
        db.rollback()

def get_article_by_url(db: Session, url: str):
    article = db.query(ArticleModel).filter(ArticleModel.url == url).first()
    if article:
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

def save_article(db: Session, article_data: dict, query: str = None):
    try:
        # Check if exists
        article = db.query(ArticleModel).filter(ArticleModel.url == article_data["url"]).first()
        
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
            
            # Update search queries list (Legacy JSON)
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
            db.add(article)
        
        # --- New Relational Logic ---
        if query:
            # 1. Get or Create SearchQuery
            search_query_obj = db.query(SearchQuery).filter(SearchQuery.text == query).first()
            if not search_query_obj:
                search_query_obj = SearchQuery(text=query, count=1, last_searched_at=datetime.utcnow())
                db.add(search_query_obj)
            else:
                search_query_obj.count += 1
                search_query_obj.last_searched_at = datetime.utcnow()
            
            # 2. Link to Article if not already linked
            if search_query_obj not in article.queries:
                article.queries.append(search_query_obj)

        db.commit()
    except Exception as e:
        print(f"DB Error saving article: {e}")
        db.rollback()

def search_articles_in_db(db: Session, query: str, start_date: str = None, end_date: str = None):
    # Search in Title OR Snippet (Smart Search)
    search_filter = or_(
        ArticleModel.title.ilike(f"%{query}%"),
        ArticleModel.snippet.ilike(f"%{query}%")
    )
    
    q = db.query(ArticleModel).filter(search_filter)
    
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
            "orientation_score": r.orientation_score,
            "embedding": r.embedding
        })
    return out

def get_latest_article_date(db: Session, query: str) -> Optional[datetime]:
    search_filter = or_(
        ArticleModel.title.ilike(f"%{query}%"),
        ArticleModel.snippet.ilike(f"%{query}%")
    )
    latest = db.query(func.max(ArticleModel.published_at)).filter(search_filter).scalar()
    return latest

# --- Storie ed edizioni -------------------------------------------------------

def save_story(db: Session, story, edition_id: str = None):
    rec = db.get(StoryRecord, story.id) or StoryRecord(id=story.id)
    rec.edition_id = edition_id
    rec.query = story.query
    rec.title = story.title
    rec.score = story.score
    rec.data = json.loads(story.model_dump_json())
    db.merge(rec)
    db.commit()


def load_story(db: Session, story_id: str):
    rec = db.get(StoryRecord, story_id)
    return rec.data if rec else None


def save_edition(db: Session, edition):
    rec = EditionRecord(id=edition.id, demo=edition.demo, data=json.loads(edition.model_dump_json()))
    db.merge(rec)
    db.commit()


def latest_edition(db: Session, include_demo: bool = True):
    q = db.query(EditionRecord)
    if not include_demo:
        q = q.filter(EditionRecord.demo.is_(False))
    rec = q.order_by(EditionRecord.created_at.desc()).first()
    return rec.data if rec else None


def recent_articles(db: Session, since: datetime, limit: int = 2000):
    """Articoli recenti gia' in DB (per costruire l'edizione senza riscaricare tutto)."""
    rows = (
        db.query(ArticleModel)
        .filter(or_(ArticleModel.published_at >= since, ArticleModel.fetched_at >= since))
        .order_by(ArticleModel.fetched_at.desc())
        .limit(limit)
        .all()
    )
    return rows


# Initialize DB
init_db()
