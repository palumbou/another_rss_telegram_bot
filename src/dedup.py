"""Deduplication module for RSS Telegram Bot."""

import hashlib
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from .logging_config import create_execution_logger
from .models import FeedItem


class Deduplicator:
    """Handles deduplication of RSS feed items using DynamoDB."""

    def __init__(
        self,
        table_name: str,
        aws_region: str = "us-east-1",
        execution_id: str | None = None,
    ):
        """Initialize the Deduplicator with DynamoDB configuration.

        Args:
            table_name: Name of the DynamoDB table for deduplication
            aws_region: AWS region for DynamoDB client
            execution_id: Execution ID for logging context
        """
        self.table_name = table_name
        self.aws_region = aws_region
        self.logger = create_execution_logger("deduplicator", execution_id)
        self.dynamodb = boto3.resource("dynamodb", region_name=aws_region)
        self.table = self.dynamodb.Table(table_name)

        self.logger.info(
            "Deduplicator initialized", table_name=table_name, aws_region=aws_region
        )

    def generate_item_id(self, item: FeedItem) -> str:
        """Generate a unique identifier for a feed item.

        Uses GUID if available, otherwise creates SHA256 hash from
        feed_url + link + published_date.

        Args:
            item: The feed item to generate ID for

        Returns:
            Unique identifier string
        """
        if item.guid:
            # Use GUID when available (Requirement 5.1)
            self.logger.debug(
                "Using GUID for item ID", item_title=item.title, guid=item.guid
            )
            return item.guid

        # Fallback to hash-based ID (Requirement 5.2)
        hash_input = f"{item.feed_url}{item.link}{item.published.isoformat()}"
        item_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        self.logger.debug(
            "Generated hash-based item ID",
            item_title=item.title,
            hash_input_length=len(hash_input),
            item_id=item_id[:16] + "...",
        )  # Log only first 16 chars for brevity
        return item_id

    def is_duplicate(self, item_id: str) -> bool:
        """Check if an item already exists in DynamoDB.

        Args:
            item_id: The unique identifier to check

        Returns:
            True if item exists, False otherwise
        """
        try:
            response = self.table.get_item(Key={"item_id": item_id})
            is_duplicate = "Item" in response
            self.logger.debug(
                "Checked for duplicate",
                item_id=item_id[:16] + "...",
                is_duplicate=is_duplicate,
            )
            return is_duplicate
        except ClientError as e:
            self.logger.error(
                f"Error checking for duplicate item {item_id}: {e}",
                item_id=item_id[:16] + "...",
                error=str(e),
            )
            # In case of error, assume it's not a duplicate to avoid blocking
            # new content
            return False

    def store_item(self, item_id: str, item: FeedItem) -> None:
        """Store a new item in DynamoDB with TTL.

        Args:
            item_id: The unique identifier for the item
            item: The feed item to store
        """
        try:
            # Calculate TTL (90 days from now)
            ttl_timestamp = int((datetime.now() + timedelta(days=90)).timestamp())

            # Store item in DynamoDB
            self.table.put_item(
                Item={
                    "item_id": item_id,
                    "feed_url": item.feed_url,
                    "link": item.link,
                    "title": item.title,
                    "processed_at": datetime.now().isoformat(),
                    "ttl": ttl_timestamp,
                }
            )
            self.logger.info(
                "Stored item in DynamoDB",
                item_id=item_id[:16] + "...",
                item_title=item.title,
                ttl_timestamp=ttl_timestamp,
            )

        except ClientError as e:
            self.logger.error(
                f"Error storing item {item_id}: {e}",
                item_id=item_id[:16] + "...",
                item_title=item.title,
                error=str(e),
            )
            raise
