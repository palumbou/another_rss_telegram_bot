"""Data models for RSS Telegram Bot."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class FeedItem:
    """Represents a single RSS/Atom feed item."""

    title: str
    link: str
    published: datetime
    content: str
    feed_url: str
    guid: str | None = None


@dataclass
class Summary:
    """Represents a formatted summary."""

    title: str
    bullets: list[str]  # Max 3 elementi, 15 parole ciascuno
    why_it_matters: str  # Max 20 parole
