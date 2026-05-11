"""Collection orchestrator - runs all crawlers and stores results."""
import json
import logging
from datetime import datetime
from typing import List
import yaml
from sqlalchemy.orm import Session
from app.models import Article
from app.crawlers.rss import RSSCrawler
from app.crawlers.github import GitHubTrendingCrawler

logger = logging.getLogger(__name__)


def load_sources_config(path: str = "config/sources.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_collection(db: Session, config_path: str = "config/sources.yaml") -> dict:
    """
    Run all crawlers, deduplicate, and store new articles.
    Returns stats: {total_fetched, new_saved, errors, by_source: {...}}
    """
    config = load_sources_config(config_path)
    all_raw: List[dict] = []
    errors = []
    stats_by_source = {}

    # RSS sources
    for src in config.get("rss_sources", []):
        try:
            crawler = RSSCrawler(
                name=src["name"],
                url=src["url"],
                category=src.get("category", "uncategorized"),
                filter_mode=src.get("filter_mode", "all"),
                keywords=src.get("keywords", []),
            )
            items = crawler.fetch()
            all_raw.extend(items)
            stats_by_source[src["name"]] = len(items)
        except Exception as e:
            logger.error(f"Error crawling RSS {src['name']}: {e}", exc_info=True)
            errors.append({"source": src["name"], "error": str(e)})
            stats_by_source[src["name"]] = 0

    # GitHub Trending sources
    for src in config.get("github_trending_sources", []):
        try:
            crawler = GitHubTrendingCrawler(
                name=src["name"],
                topic=src["topic"],
                category=src.get("category", "uncategorized"),
            )
            items = crawler.fetch()
            all_raw.extend(items)
            stats_by_source[src["name"]] = len(items)
        except Exception as e:
            logger.error(f"Error crawling GitHub Trending {src['name']}: {e}", exc_info=True)
            errors.append({"source": src["name"], "error": str(e)})
            stats_by_source[src["name"]] = 0

    # Deduplicate by URL and store
    new_saved = 0
    now = datetime.utcnow()
    seen_urls = set()
    for raw in all_raw:
        url = raw.get("url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)

        existing = db.query(Article).filter(Article.url == url).first()
        if existing:
            continue

        try:
            article = Article(
                source=raw["source"],
                source_type=raw["source_type"],
                title=raw["title"],
                url=url,
                summary=raw.get("summary"),
                category=raw.get("category"),
                tags=raw.get("tags", "[]"),
                published_at=raw.get("published_at"),
                fetched_at=raw.get("fetched_at", now),
                raw_content=raw.get("raw_content"),
            )
            db.add(article)
            new_saved += 1
        except Exception as e:
            logger.warning(f"Failed to save article {url}: {e}")
            db.rollback()

    db.commit()

    result = {
        "total_fetched": len(all_raw),
        "new_saved": new_saved,
        "errors": errors,
        "by_source": stats_by_source,
    }
    logger.info(f"Collection done: {new_saved} new / {len(all_raw)} fetched, {len(errors)} errors")
    return result
