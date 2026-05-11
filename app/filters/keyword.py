"""Keyword filtering engine."""
import json
import logging
from typing import List

logger = logging.getLogger(__name__)


def matches_keywords(text: str, keywords: List[str]) -> bool:
    """Check if text contains any of the keywords (case-insensitive)."""
    if not keywords:
        return True
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def filter_article(article: dict, filter_mode: str, keywords: List[str]) -> bool:
    """
    Decide whether to keep an article.
    filter_mode:
      - "all": keep everything
      - "keyword": keep only if title/summary matches keywords
    """
    if filter_mode == "all":
        return True
    if filter_mode == "keyword":
        text = f"{article.get('title', '')} {article.get('summary', '')}"
        return matches_keywords(text, keywords)
    return True
