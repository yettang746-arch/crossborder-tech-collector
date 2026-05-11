"""API v1 routes - articles, stats, health."""
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db import get_db
from app.models import Article
from app.collector import run_collection

router = APIRouter(prefix="/api/v1", tags=["v1"])


# --- Schemas ---

class ArticleResponse(BaseModel):
    id: int
    source: str
    source_type: str
    title: str
    url: str
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    date: str
    total_articles: int
    sources: dict
    categories: dict


class CollectResponse(BaseModel):
    total_fetched: int
    new_saved: int
    errors: list
    by_source: dict


class HealthResponse(BaseModel):
    status: str
    db_path: str
    article_count: int


# --- Routes ---

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    count = db.query(func.count(Article.id)).scalar()
    return HealthResponse(
        status="ok",
        db_path=os.getenv("DB_PATH", "/app/data/collector.db"),
        article_count=count,
    )


@router.get("/articles", response_model=list[ArticleResponse])
def get_articles(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source name"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Article)

    if date:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            next_day = dt + timedelta(days=1)
            query = query.filter(Article.fetched_at >= dt, Article.fetched_at < next_day)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if category:
        query = query.filter(Article.category == category)

    if source:
        # Support partial match
        query = query.filter(Article.source.contains(source))

    query = query.order_by(Article.fetched_at.desc())
    articles = query.offset(offset).limit(limit).all()
    return articles


@router.get("/articles/stats", response_model=StatsResponse)
def get_stats(
    date: Optional[str] = Query(None, description="Stats for date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    query = db.query(Article)

    if date:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            next_day = dt + timedelta(days=1)
            query = query.filter(Article.fetched_at >= dt, Article.fetched_at < next_day)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    else:
        # Default: today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        next_day = today + timedelta(days=1)
        query = query.filter(Article.fetched_at >= today, Article.fetched_at < next_day)
        date = today.strftime("%Y-%m-%d")

    articles = query.all()

    sources = {}
    categories = {}
    for a in articles:
        sources[a.source] = sources.get(a.source, 0) + 1
        cat = a.category or "uncategorized"
        categories[cat] = categories.get(cat, 0) + 1

    return StatsResponse(
        date=date,
        total_articles=len(articles),
        sources=sources,
        categories=categories,
    )


@router.post("/collect", response_model=CollectResponse)
def trigger_collect(db: Session = Depends(get_db)):
    """Manually trigger a collection run."""
    result = run_collection(db)
    return CollectResponse(**result)
