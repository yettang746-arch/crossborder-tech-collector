"""RSS feed crawler."""
import logging
from datetime import datetime
from typing import List
import feedparser
import httpx
from app.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)


class RSSCrawler(BaseCrawler):
    """Crawl a single RSS feed and return parsed entries."""

    def __init__(self, name: str, url: str, category: str = "uncategorized",
                 filter_mode: str = "all", keywords: List[str] = None):
        self._name = name
        self._url = url
        self._category = category
        self._filter_mode = filter_mode
        self._keywords = [k.lower() for k in (keywords or [])]

    @property
    def source_type(self) -> str:
        return "rss"

    def fetch(self) -> List[dict]:
        logger.info(f"[RSS] Fetching: {self._name} ({self._url})")
        try:
            # Use httpx with browser UA, then pass to feedparser
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            }
            resp = httpx.get(self._url, timeout=30, follow_redirects=True, headers=headers)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
        except Exception as e:
            logger.error(f"[RSS] Failed to fetch {self._name}: {e}")
            return []

        if feed.bozo and not feed.entries:
            logger.warning(f"[RSS] Parse error for {self._name}: {feed.bozo_exception}")
            return []

        results = []
        now = datetime.utcnow()
        for entry in feed.entries:
            # Skip entries older than 7 days for non-filtered ("all") sources
            if self._filter_mode == "all" and self._category != "uncategorized":
                pub_date = None
                for field in ("published_parsed", "updated_parsed"):
                    tp = entry.get(field)
                    if tp:
                        try:
                            pub_date = datetime(*tp[:6])
                        except Exception:
                            pass
                        break
                if pub_date and (now - pub_date).days > 7:
                    continue
            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()
            if not title or not url:
                continue

            summary = entry.get("summary", "")
            # Clean HTML tags from summary (basic)
            if summary:
                import re
                summary = re.sub(r"<[^>]+>", "", summary).strip()[:500]

            published_at = None
            for field in ("published_parsed", "updated_parsed"):
                tp = entry.get(field)
                if tp:
                    try:
                        published_at = datetime(*tp[:6])
                    except Exception:
                        pass
                    break

            text_to_check = f"{title} {summary}".lower()

            # Apply filter
            if self._filter_mode == "keyword" and self._keywords:
                if not any(kw in text_to_check for kw in self._keywords):
                    continue

            results.append({
                "source": self._name,
                "source_type": "rss",
                "title": title,
                "url": url,
                "summary": summary or None,
                "category": self._category,
                "tags": "[]",
                "published_at": published_at,
                "fetched_at": now,
                "raw_content": None,
            })

        logger.info(f"[RSS] {self._name}: {len(results)} articles (after filter)")
        return results
