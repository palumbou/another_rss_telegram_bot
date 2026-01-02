"""Telegram Publisher for RSS Telegram Bot."""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .config import TelegramConfig
from .logging_config import create_execution_logger
from .models import Summary


class TelegramPublisher:
    """Handles publishing messages to Telegram."""

    def __init__(self, config: TelegramConfig, execution_id: str | None = None):
        """Initialize Telegram publisher with configuration."""
        self.config = config
        self.logger = create_execution_logger("telegram_publisher", execution_id)
        self.base_url = f"https://api.telegram.org/bot{config.bot_token}"

        self.logger.info(
            "TelegramPublisher initialized",
            chat_id=config.chat_id,
            parse_mode=config.parse_mode,
            retry_attempts=config.retry_attempts,
        )

    def send_message(self, summary: Summary, original_link: str) -> bool:
        """
        Send a formatted message to Telegram.

        Args:
            summary: The summary to send
            original_link: Link to the original article

        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            self.logger.info(
                "Preparing to send message",
                summary_title=summary.title,
                original_link=original_link,
            )
            message = self.format_message(summary, original_link)
            success = self._send_telegram_message(message)

            if success:
                self.logger.info(
                    "Message sent successfully", summary_title=summary.title
                )
            else:
                self.logger.error("Failed to send message", summary_title=summary.title)

            return success
        except Exception as e:
            self.logger.error(
                f"Failed to send message: {e}",
                summary_title=summary.title,
                error=str(e),
            )
            return False

    def format_message(self, summary: Summary, link: str) -> str:
        """
        Format a message for Telegram with HTML parsing.

        Args:
            summary: The summary to format
            link: Link to the original article

        Returns:
            Formatted HTML message
        """
        # Escape HTML characters in text content
        title = self._escape_html(summary.title)
        bullets = [self._escape_html(bullet) for bullet in summary.bullets]
        why_it_matters = self._escape_html(summary.why_it_matters)

        # Format message with HTML
        message = f"<b>{title}</b>\n\n"

        for bullet in bullets:
            message += f"• {bullet}\n"

        message += f"\n<i>Perché conta:</i> {why_it_matters}\n\n"
        message += f'🔗 <a href="{link}">Leggi l\'articolo completo</a>'

        return message

    def handle_rate_limit(self, retry_count: int) -> None:
        """
        Handle rate limiting with exponential backoff.

        Args:
            retry_count: Current retry attempt number
        """
        backoff_time = self.config.backoff_factor**retry_count
        self.logger.warning(
            f"Rate limited, waiting {backoff_time} seconds before retry {retry_count + 1}",
            retry_count=retry_count,
            backoff_time=backoff_time,
        )
        time.sleep(backoff_time)

    def _send_telegram_message(self, message: str) -> bool:
        """
        Send message to Telegram API with retry logic.

        Args:
            message: Formatted message to send

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/sendMessage"

        data = {
            "chat_id": self.config.chat_id,
            "text": message,
            "parse_mode": self.config.parse_mode,
            "disable_web_page_preview": False,
        }

        for attempt in range(self.config.retry_attempts):
            try:
                self.logger.debug(
                    f"Sending message to Telegram API (attempt {attempt + 1})",
                    attempt=attempt + 1,
                    message_length=len(message),
                )

                # Encode data as JSON
                json_data = json.dumps(data).encode("utf-8")

                # Create request
                req = urllib.request.Request(
                    url,
                    data=json_data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "RSS-Telegram-Bot/1.0",
                    },
                )

                # Send request
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status == 200:
                        self.logger.info(
                            "Message sent successfully to Telegram",
                            status_code=response.status,
                        )
                        return True
                    else:
                        self.logger.error(
                            f"Telegram API returned status {response.status}",
                            status_code=response.status,
                        )
                        return False

            except urllib.error.HTTPError as e:
                if e.code == 429:  # Rate limiting
                    self.logger.warning(
                        f"Rate limited by Telegram API (attempt {attempt + 1})",
                        attempt=attempt + 1,
                        http_code=e.code,
                    )
                    if attempt < self.config.retry_attempts - 1:
                        self.handle_rate_limit(attempt)
                        continue
                    else:
                        self.logger.error(
                            "Max retry attempts reached for rate limiting"
                        )
                        return False
                else:
                    self.logger.error(
                        f"HTTP error sending message: {e.code} - {e.reason}",
                        http_code=e.code,
                        http_reason=e.reason,
                    )
                    # For non-rate-limit errors, continue processing other messages
                    return False

            except urllib.error.URLError as e:
                self.logger.error(
                    f"URL error sending message: {e.reason}", error_reason=str(e.reason)
                )
                return False

            except Exception as e:
                self.logger.error(
                    f"Unexpected error sending message: {e}", error=str(e)
                )
                return False

        return False

    def _escape_html(self, text: str) -> str:
        """
        Escape HTML characters in text for Telegram HTML parsing.

        Args:
            text: Text to escape

        Returns:
            HTML-escaped text
        """
        if not text:
            return ""

        # Escape HTML characters
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")

        return text
