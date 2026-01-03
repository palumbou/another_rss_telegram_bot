"""Configuration management for RSS Telegram Bot."""

import os
from dataclasses import dataclass


@dataclass
class TelegramConfig:
    """Configuration for Telegram Bot API."""

    bot_token: str
    chat_id: str
    parse_mode: str = "HTML"
    retry_attempts: int = 3
    backoff_factor: float = 2.0


@dataclass
class BedrockConfig:
    """Configuration for Amazon Bedrock."""

    model_id: str = "eu.meta.llama3-2-1b-instruct-v1:0"
    region: str = "us-east-1"
    max_tokens: int = 1000


@dataclass
class ScheduleConfig:
    """Configuration for scheduled execution."""

    timezone: str = "Europe/Rome"
    hour: int = 9
    minute: int = 0


class Config:
    """Main configuration manager."""

    # Default AWS feeds
    DEFAULT_AWS_FEEDS = [
        "https://aws.amazon.com/blogs/aws/feed/",
        "https://aws.amazon.com/about-aws/whats-new/recent/feed/",
        "https://aws.amazon.com/blogs/security/feed/",
        "https://aws.amazon.com/blogs/compute/feed/",
        "https://aws.amazon.com/blogs/database/feed/",
    ]

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.telegram_secret_name = os.getenv(
            "TELEGRAM_SECRET_NAME", "rss-telegram-bot-token"
        )
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.dynamodb_table = os.getenv("DYNAMODB_TABLE", "rss-telegram-dedup")
        self.aws_region = os.getenv("CURRENT_AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

    def get_feed_urls(self) -> list[str]:
        """Get RSS feed URLs from environment or use defaults."""
        feed_urls_env = os.getenv("RSS_FEED_URLS", "")
        if feed_urls_env:
            return [url.strip() for url in feed_urls_env.split(",") if url.strip()]
        return self.DEFAULT_AWS_FEEDS

    def get_telegram_config(self) -> TelegramConfig:
        """Get Telegram configuration."""
        # Token will be retrieved from Secrets Manager at runtime
        return TelegramConfig(
            bot_token="",  # Will be populated from Secrets Manager
            chat_id=self.chat_id,
        )

    def get_bedrock_config(self) -> BedrockConfig:
        """Get Bedrock configuration."""
        return BedrockConfig(region=self.aws_region)

    def get_schedule_config(self) -> ScheduleConfig:
        """Get schedule configuration."""
        return ScheduleConfig()
