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

    # Telegram hard limit is 4096 characters per message; keep a safety margin
    MAX_MESSAGE_LENGTH = 4000

    def __init__(self, config: TelegramConfig, execution_id: str | None = None):
        """Initialize Telegram publisher with configuration."""
        self.config = config
        self.logger = create_execution_logger("telegram_publisher", execution_id)
        self.base_url = f"https://api.telegram.org/bot{config.bot_token}"

        self.logger.info(
            "TelegramPublisher initialized",
            chat_id=config.chat_id,
            message_thread_id=config.message_thread_id,
            parse_mode=config.parse_mode,
            retry_attempts=config.retry_attempts,
        )

    def send_message(self, summary: Summary, original_link: str, source_url: str = "") -> bool:
        """
        Send a formatted message to Telegram.

        Args:
            summary: The summary to send
            original_link: Link to the original article
            source_url: URL of the RSS feed source (optional)

        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            self.logger.info(
                "Preparing to send message",
                summary_title=summary.title,
                original_link=original_link,
                source_url=source_url,
            )
            message = self.format_message(summary, original_link, source_url)
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

    def format_message(self, summary: Summary, link: str, source_url: str = "") -> str:
        """
        Format a message for Telegram with HTML parsing.

        Args:
            summary: The summary to format
            link: Link to the original article
            source_url: URL of the RSS feed source (optional)

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
        
        # Add source information if available
        if source_url:
            source_name = self._extract_source_name(source_url)
            if source_name:
                message += f"\n📰 <i>Fonte: {source_name}</i>"
        
        # Add model metadata if available
        if summary.model_used:
            message += f"\n\n<code>━━━━━━━━━━━━━━━━━━━━</code>"
            message += f"\n🤖 <i>Modello: {self._format_model_name(summary.model_used)}</i>"

            # Add tokens if available
            if summary.tokens_used is not None:
                message += f"\n🔢 <i>Token: {summary.tokens_used}</i>"

            # Add response time if available
            if summary.response_time_ms is not None:
                if summary.response_time_ms < 1000:
                    time_display = f"{summary.response_time_ms}ms"
                else:
                    time_display = f"{summary.response_time_ms / 1000:.2f}s"
                message += f"\n⚡ <i>Tempo: {time_display}</i>"

        return message

    def send_digest(self, entries: list[tuple[Summary, str, str]]) -> int:
        """
        Send all news items as a single combined digest message.

        If the digest exceeds Telegram's message length limit, it is split
        into multiple parts at item boundaries (HTML is never broken mid-tag).

        Args:
            entries: List of (summary, original_link, source_url) tuples

        Returns:
            Number of Telegram messages successfully sent (0 on failure)
        """
        if not entries:
            return 0

        try:
            messages = self._build_digest_messages(entries)
            self.logger.info(
                "Sending digest",
                item_count=len(entries),
                message_count=len(messages),
            )

            sent = 0
            for message in messages:
                if self._send_telegram_message(message):
                    sent += 1
                else:
                    self.logger.error(
                        "Failed to send digest part",
                        part=sent + 1,
                        total_parts=len(messages),
                    )

            return sent
        except Exception as e:
            self.logger.error(f"Failed to send digest: {e}", error=str(e))
            return 0

    def _build_digest_messages(
        self, entries: list[tuple[Summary, str, str]]
    ) -> list[str]:
        """
        Build the digest message(s), splitting at item boundaries when the
        Telegram length limit would be exceeded.

        Args:
            entries: List of (summary, original_link, source_url) tuples

        Returns:
            List of formatted HTML messages ready to send
        """
        header = f"📬 <b>Rassegna del giorno — {len(entries)} notizie</b>\n\n"
        footer = self._format_digest_footer(entries)

        blocks = [
            self._format_digest_entry(i + 1, summary, link, source_url)
            for i, (summary, link, source_url) in enumerate(entries)
        ]

        messages = []
        current = header
        for block in blocks:
            candidate = current + block if current else block
            if len(candidate) + len(footer) > self.MAX_MESSAGE_LENGTH and current not in ("", header):
                messages.append(current.rstrip())
                current = block
            else:
                current = candidate
        if current:
            messages.append((current + footer).rstrip())

        # Mark parts when the digest is split across multiple messages
        if len(messages) > 1:
            messages = [
                f"{msg}\n\n<i>(parte {i + 1}/{len(messages)})</i>"
                for i, msg in enumerate(messages)
            ]

        return messages

    def _format_digest_entry(
        self, index: int, summary: Summary, link: str, source_url: str
    ) -> str:
        """Format a single news item as a compact digest block."""
        title = self._escape_html(summary.title)
        bullets = [self._escape_html(bullet) for bullet in summary.bullets]
        why_it_matters = self._escape_html(summary.why_it_matters)

        block = f"<b>{index}. {title}</b>\n"
        for bullet in bullets:
            block += f"• {bullet}\n"
        block += f"<i>Perché conta:</i> {why_it_matters}\n"
        block += f'🔗 <a href="{link}">Leggi l\'articolo completo</a>'

        if source_url:
            source_name = self._extract_source_name(source_url)
            if source_name:
                block += f" — 📰 <i>{source_name}</i>"

        return block + "\n\n"

    def _format_digest_footer(self, entries: list[tuple[Summary, str, str]]) -> str:
        """Format a single aggregate metadata footer for the digest."""
        summaries = [entry[0] for entry in entries]
        model_used = next((s.model_used for s in summaries if s.model_used), None)
        if not model_used:
            return ""

        footer = "\n<code>━━━━━━━━━━━━━━━━━━━━</code>"
        footer += f"\n🤖 <i>Modello: {self._format_model_name(model_used)}</i>"

        total_tokens = sum(s.tokens_used for s in summaries if s.tokens_used is not None)
        if total_tokens:
            footer += f"\n🔢 <i>Token totali: {total_tokens}</i>"

        return footer

    def _format_model_name(self, model_used: str) -> str:
        """Map a model ID to a human-friendly display name."""
        model_display = model_used
        if "amazon.nova" in model_display.lower():
            if "nova-2-pro" in model_display.lower():
                model_display = "Amazon Nova 2 Pro"
            elif "nova-2-lite" in model_display.lower():
                model_display = "Amazon Nova 2 Lite"
            elif "nova-2-sonic" in model_display.lower():
                model_display = "Amazon Nova 2 Sonic"
            else:
                model_display = "Amazon Nova Micro"
        elif "mistral" in model_display.lower():
            if "large-3" in model_display.lower():
                model_display = "Mistral Large 3 (675B MoE)"
            elif "large-2402" in model_display.lower():
                model_display = "Mistral Large (24.02)"
            elif "large-2407" in model_display.lower():
                model_display = "Mistral Large (24.07)"
            else:
                model_display = "Mistral Large"
        elif "llama" in model_display.lower():
            model_display = "Llama 3.2 3B"
        elif model_display == "fallback":
            model_display = "Extractive (Fallback)"
        elif model_display == "error":
            model_display = "Error (Emergency Fallback)"

        return model_display

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

        # Optional forum topic targeting: only add the field when configured,
        # so the payload stays identical to previous versions otherwise
        if self.config.message_thread_id:
            try:
                data["message_thread_id"] = int(self.config.message_thread_id)
            except ValueError:
                self.logger.warning(
                    "Invalid message_thread_id, sending without topic targeting",
                    message_thread_id=self.config.message_thread_id,
                )

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

    def _extract_source_name(self, feed_url: str) -> str:
        """
        Extract a clean source name from a feed URL.

        Args:
            feed_url: The RSS feed URL

        Returns:
            Clean source name for display
        """
        if not feed_url:
            return ""

        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(feed_url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes
            if domain.startswith('www.'):
                domain = domain[4:]
            if domain.startswith('feeds.'):
                domain = domain[6:]
            
            # Map common domains to friendly names
            domain_mapping = {
                'github.com': 'GitHub Blog',
                'aws.amazon.com': 'AWS Blog',
                'feedburner.com': 'O\'Reilly Radar',  # Common for O'Reilly feeds
                'feeds.feedburner.com': 'O\'Reilly Radar',
                'techcrunch.com': 'TechCrunch',
                'blog.google': 'Google Blog',
                'microsoft.com': 'Microsoft Blog',
                'apple.com': 'Apple Newsroom',
                'meta.com': 'Meta Blog',
                'openai.com': 'OpenAI Blog',
                'anthropic.com': 'Anthropic Blog',
            }
            
            # Check for exact matches first
            if domain in domain_mapping:
                return domain_mapping[domain]
            
            # Check for partial matches
            for key, value in domain_mapping.items():
                if key in domain or domain in key:
                    return value
            
            # For unknown domains, create a clean name
            # Remove common TLDs and capitalize
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                main_domain = domain_parts[-2]  # Get the main part before TLD
                return main_domain.capitalize()
            
            return domain.capitalize()
            
        except Exception:
            # If anything fails, return empty string
            return ""
