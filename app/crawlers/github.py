"""GitHub Trending crawler - scrapes github.com/trending."""
import logging
from datetime import datetime
from typing import List
import httpx
from bs4 import BeautifulSoup
from app.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

GITHUB_TRENDING_URL = "https://github.com/trending?since=daily&topic={topic}"


class GitHubTrendingCrawler(BaseCrawler):
    """Scrape GitHub Trending page for a given topic."""

    def __init__(self, name: str, topic: str, category: str = "uncategorized"):
        self._name = name
        self._topic = topic
        self._category = category

    @property
    def source_type(self) -> str:
        return "github_trending"

    def fetch(self) -> List[dict]:
        url = GITHUB_TRENDING_URL.format(topic=self._topic)
        logger.info(f"[GitHub] Fetching trending: {self._topic} ({url})")

        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True,
                             headers={"Accept": "text/html"})
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"[GitHub] Failed to fetch trending/{self._topic}: {e}")
            return []

        return self._parse(resp.text)

    def _parse(self, html: str) -> List[dict]:
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.select("article.Box-row")
        if not articles:
            # Try newer GitHub layout
            articles = soup.select("article")
            articles = [a for a in articles if a.get("id") or a.select_one("h2 a")]

        now = datetime.utcnow()
        results = []

        for article in articles:
            # Extract repo link
            link_el = article.select_one("h2 a") or article.select_one("a[href]")
            if not link_el:
                continue

            href = link_el.get("href", "").strip()
            if not href:
                continue
            repo_url = f"https://github.com{href}" if href.startswith("/") else href

            # Title = repo name (owner/repo)
            title = href.strip("/")

            # Description
            desc_el = article.select_one("p")
            summary = desc_el.get_text(strip=True)[:300] if desc_el else None

            # Stars / language
            tags = []
            lang_el = article.select_one("[itemprop='programmingLanguage']")
            if lang_el:
                lang = lang_el.get_text(strip=True)
                if lang:
                    tags.append(lang)

            stars_el = article.select_one("a.Link--muted[href$='/stargazers']")
            if stars_el:
                star_text = stars_el.get_text(strip=True).replace(",", "")
                try:
                    tags.append(f"{int(star_text)}★")
                except ValueError:
                    pass

            results.append({
                "source": self._name,
                "source_type": "github_trending",
                "title": title,
                "url": repo_url,
                "summary": summary,
                "category": self._category,
                "tags": str(tags) if tags else "[]",
                "published_at": None,  # Trending has no publish date
                "fetched_at": now,
                "raw_content": None,
            })

        logger.info(f"[GitHub] trending/{self._topic}: {len(results)} repos")
        return results
