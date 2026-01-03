"""Configuration management for RSS Telegram Bot."""

import json
import os
from dataclasses import dataclass
from pathlib import Path


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

    model_id: str = "amazon.nova-micro-v1:0"
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

    # Default feeds file path
    FEEDS_FILE = "feeds.json"

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.telegram_secret_name = os.getenv(
            "TELEGRAM_SECRET_NAME", "rss-telegram-bot-token"
        )
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.dynamodb_table = os.getenv("DYNAMODB_TABLE", "rss-telegram-dedup")
        self.aws_region = os.getenv("CURRENT_AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        self.bedrock_model_id = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")

    def get_feed_urls(self) -> list[str]:
        """Get RSS feed URLs from feeds.json file."""
        # Try to find feeds.json in current directory or Lambda root
        feeds_file = Path(self.FEEDS_FILE)
        if not feeds_file.exists():
            # Try in Lambda root directory
            feeds_file = Path("/var/task") / self.FEEDS_FILE
        
        if not feeds_file.exists():
            raise FileNotFoundError(f"Feeds file not found: {self.FEEDS_FILE}")
        
        try:
            with open(feeds_file, "r") as f:
                data = json.load(f)
            
            # Extract enabled feeds
            feeds = data.get("feeds", [])
            enabled_urls = [
                feed["url"]
                for feed in feeds
                if feed.get("enabled", True) and "url" in feed
            ]
            
            if not enabled_urls:
                raise ValueError("No enabled feeds found in feeds.json")
            
            return enabled_urls
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in feeds file: {e}")
        except Exception as e:
            raise ValueError(f"Error reading feeds file: {e}")

    def get_telegram_config(self) -> TelegramConfig:
        """Get Telegram configuration."""
        # Token will be retrieved from Secrets Manager at runtime
        return TelegramConfig(
            bot_token="",  # Will be populated from Secrets Manager
            chat_id=self.chat_id,
        )

    def get_bedrock_config(self) -> BedrockConfig:
        """Get Bedrock configuration."""
        return BedrockConfig(
            model_id=self.bedrock_model_id,
            region=self.aws_region
        )

    def get_schedule_config(self) -> ScheduleConfig:
        """Get schedule configuration."""
        return ScheduleConfig()
