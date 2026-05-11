"""SQLAlchemy models."""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, String, DateTime, Index
from app.db import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # rss / github_trending / web_scraper
    title = Column(Text, nullable=False)
    url = Column(Text, unique=True, nullable=False)
    summary = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    tags = Column(Text, nullable=True)  # JSON array string
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    raw_content = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_articles_fetched", "fetched_at"),
        Index("idx_articles_source", "source"),
        Index("idx_articles_category", "category"),
    )

    def __repr__(self):
        return f"<Article(source={self.source}, title={self.title[:50]})>"
