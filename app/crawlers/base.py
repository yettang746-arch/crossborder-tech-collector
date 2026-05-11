"""Base crawler interface."""
from abc import ABC, abstractmethod
from typing import List
from app.models import Article


class BaseCrawler(ABC):
    """All crawlers inherit from this."""

    @abstractmethod
    def fetch(self) -> List[dict]:
        """
        Fetch raw data from source.
        Returns list of dicts matching Article fields:
        {source, source_type, title, url, summary, category, tags, published_at}
        """
        ...

    def normalize(self, raw: dict) -> dict:
        """Ensure required fields exist, fill defaults."""
        raw.setdefault("source_type", self.source_type)
        raw.setdefault("category", "uncategorized")
        raw.setdefault("tags", "[]")
        raw.setdefault("summary", None)
        raw.setdefault("published_at", None)
        raw.setdefault("raw_content", None)
        return raw

    @property
    @abstractmethod
    def source_type(self) -> str:
        ...
