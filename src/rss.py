"""RSS Feed Processing module for RSS Telegram Bot."""

from datetime import datetime
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from .logging_config import create_execution_logger
from .models import FeedItem


class FeedProcessor:
    """Handles RSS/Atom feed processing and normalization."""

    def __init__(self, timeout: int = 30, execution_id: str | None = None):
        """Initialize FeedProcessor with configuration.

        Args:
            timeout: HTTP request timeout in seconds
            execution_id: Execution ID for logging context
        """
        self.timeout = timeout
        self.logger = create_execution_logger("feed_processor", execution_id)
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "RSS-Telegram-Bot/1.0 (Generic RSS to Telegram Bot)"}
        )

        self.logger.info("FeedProcessor initialized", timeout=timeout)

    def fetch_feeds(self, feed_urls: list[str]) -> list[FeedItem]:
        """Fetch and parse multiple RSS/Atom feeds.

        Args:
            feed_urls: List of RSS/Atom feed URLs to process

        Returns:
            List of FeedItem objects from all feeds
        """
        self.logger.log_execution_start(feed_count=len(feed_urls))
        all_items = []

        for feed_url in feed_urls:
            try:
                items = self.parse_feed(feed_url)
                all_items.extend(items)
                self.logger.log_feed_processing(feed_url, len(items))
            except Exception as e:
                self.logger.error(
                    f"Failed to parse feed {feed_url}: {e}",
                    feed_url=feed_url,
                    error=str(e),
                )
                continue

        self.logger.log_execution_end(success=True, total_items=len(all_items))
        return all_items

    def parse_feed(self, feed_url: str) -> list[FeedItem]:
        """Parse a single RSS/Atom feed.

        Args:
            feed_url: URL of the RSS/Atom feed

        Returns:
            List of FeedItem objects from the feed

        Raises:
            ValueError: If feed URL is not HTTPS
            requests.RequestException: If feed download fails
        """
        self.logger.info("Starting to parse feed", feed_url=feed_url)

        # Validate HTTPS requirement
        parsed_url = urlparse(feed_url)
        if parsed_url.scheme != "https":
            error_msg = f"Feed URL must use HTTPS protocol: {feed_url}"
            self.logger.error(error_msg, feed_url=feed_url, scheme=parsed_url.scheme)
            raise ValueError(error_msg)

        # Download feed content
        try:
            self.logger.info("Downloading feed content", feed_url=feed_url)
            response = self.session.get(feed_url, timeout=self.timeout)
            response.raise_for_status()
            self.logger.info(
                "Feed downloaded successfully",
                feed_url=feed_url,
                status_code=response.status_code,
                content_length=len(response.content),
            )
        except requests.RequestException as e:
            self.logger.error(
                f"Failed to download feed {feed_url}: {e}",
                feed_url=feed_url,
                error=str(e),
            )
            raise

        # Parse feed with feedparser
        self.logger.info("Parsing feed content", feed_url=feed_url)
        feed = feedparser.parse(response.content)

        if feed.bozo and hasattr(feed, "bozo_exception"):
            self.logger.warning(
                f"Feed parsing warning for {feed_url}: {feed.bozo_exception}",
                feed_url=feed_url,
                bozo_exception=str(feed.bozo_exception),
            )

        items = []
        for entry in feed.entries:
            try:
                item = self.normalize_item(entry, feed_url)
                items.append(item)
            except Exception as e:
                self.logger.warning(
                    f"Failed to normalize entry from {feed_url}: {e}",
                    feed_url=feed_url,
                    error=str(e),
                )
                continue

        self.logger.info(
            "Successfully parsed feed",
            feed_url=feed_url,
            items_count=len(items),
            total_entries=len(feed.entries),
        )
        return items

    def normalize_item(self, raw_item: dict, feed_url: str) -> FeedItem:
        """Normalize a raw feed entry into a FeedItem.

        Args:
            raw_item: Raw feed entry from feedparser
            feed_url: Source feed URL

        Returns:
            Normalized FeedItem object
        """
        # Extract title
        title = getattr(raw_item, "title", "No Title")

        # Extract link
        link = getattr(raw_item, "link", "")

        # Extract and parse published date
        published_str = None
        if hasattr(raw_item, "published") and raw_item.published:
            published_str = raw_item.published

        if published_str:
            try:
                # Try to parse with dateutil (handles most RSS/Atom formats)
                published = date_parser.parse(published_str)
                # Ensure timezone-aware datetime
                if published.tzinfo is None:
                    published = published.replace(
                        tzinfo=datetime.now().astimezone().tzinfo
                    )
            except (ValueError, TypeError):
                published = datetime.now()
        else:
            published = datetime.now()

        # Extract content (try summary first, then description)
        content = ""
        if hasattr(raw_item, "summary") and raw_item.summary:
            content = raw_item.summary
        elif hasattr(raw_item, "description") and raw_item.description:
            content = raw_item.description
        elif hasattr(raw_item, "content") and raw_item.content:
            # Handle content list from Atom feeds
            if isinstance(raw_item.content, list) and raw_item.content:
                content = raw_item.content[0].get("value", "")
            else:
                content = str(raw_item.content)

        # Clean HTML from content
        content = self.clean_html_content(content)

        # Extract GUID
        guid = None
        if hasattr(raw_item, "id") and raw_item.id:
            guid = raw_item.id
        elif hasattr(raw_item, "guid") and raw_item.guid:
            guid = raw_item.guid

        return FeedItem(
            title=title,
            link=link,
            published=published,
            content=content,
            feed_url=feed_url,
            guid=guid,
        )

    def clean_html_content(self, content: str) -> str:
        """Remove HTML tags from content and normalize whitespace.

        Args:
            content: Raw content that may contain HTML

        Returns:
            Clean text content without HTML tags
        """
        if not content:
            return ""

        # Check if content looks like HTML (contains < and > characters)
        if "<" not in content and ">" not in content:
            # No HTML tags, just normalize whitespace and return
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split())
            return " ".join(chunk for chunk in chunks if chunk)

        # Parse HTML and extract text
        soup = BeautifulSoup(content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text and normalize whitespace
        text = soup.get_text(separator=" ")  # Add space separator between elements

        # Remove any remaining < and > characters (for edge cases like standalone brackets)
        text = text.replace("<", "").replace(">", "")

        # Normalize whitespace (including tabs)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split())
        text = " ".join(chunk for chunk in chunks if chunk)

        return text
