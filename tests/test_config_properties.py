"""Property-based tests for configuration management."""

import os
from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st

from src.config import Config


class TestConfigProperties:
    """Property-based tests for Config class."""

    @given(
        st.lists(
            st.text(min_size=1, max_size=100).filter(
                lambda x: "," not in x and x.strip() and "\x00" not in x
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_property_1_configurable_feeds(self, feed_urls):
        """
        Property 1: Configurazione Feed Personalizzabili
        For any list of feed URLs provided as configuration parameter,
        the system should process exactly those feeds and no others.

        **Feature: another-rss-telegram-bot, Property 1: Configurazione Feed Personalizzabili**
        **Validates: Requirements 1.1, 11.5**
        """
        # Arrange: Create comma-separated feed URLs
        feed_urls_str = ",".join(feed_urls)

        # Act: Mock environment variable and get feed URLs
        with patch.dict(os.environ, {"RSS_FEED_URLS": feed_urls_str}):
            config = Config()
            result_urls = config.get_feed_urls()

        # Assert: Should return exactly the configured feeds
        expected_urls = [url.strip() for url in feed_urls if url.strip()]
        assert result_urls == expected_urls
        assert len(result_urls) == len(expected_urls)

        # Ensure no default feeds are included when custom feeds are provided
        for default_feed in Config.DEFAULT_AWS_FEEDS:
            if default_feed not in expected_urls:
                assert default_feed not in result_urls

    def test_property_1_default_feeds_when_no_config(self):
        """
        Property 1 edge case: When no custom feeds are configured,
        should return default AWS feeds.

        **Feature: another-rss-telegram-bot, Property 1: Configurazione Feed Personalizzabili**
        **Validates: Requirements 1.1, 11.5**
        """
        # Act: No RSS_FEED_URLS environment variable
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            result_urls = config.get_feed_urls()

        # Assert: Should return default AWS feeds
        assert result_urls == Config.DEFAULT_AWS_FEEDS
        assert len(result_urls) == len(Config.DEFAULT_AWS_FEEDS)

    def test_property_1_empty_config_uses_defaults(self):
        """
        Property 1 edge case: When RSS_FEED_URLS is empty,
        should return default AWS feeds.

        **Feature: another-rss-telegram-bot, Property 1: Configurazione Feed Personalizzabili**
        **Validates: Requirements 1.1, 11.5**
        """
        # Act: Empty RSS_FEED_URLS environment variable
        with patch.dict(os.environ, {"RSS_FEED_URLS": ""}):
            config = Config()
            result_urls = config.get_feed_urls()

        # Assert: Should return default AWS feeds
        assert result_urls == Config.DEFAULT_AWS_FEEDS

    @given(
        st.one_of(
            # Generate numeric chat IDs (common for Telegram)
            st.integers(min_value=-999999999999, max_value=999999999999).map(str),
            # Generate alphanumeric chat IDs (for usernames)
            st.text(
                alphabet=st.characters(
                    whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_-"
                ),
                min_size=1,
                max_size=50,
            ).filter(lambda x: x.strip() and "\x00" not in x),
        )
    )
    def test_property_2_configurable_chat_id(self, chat_id):
        """
        Property 2: Utilizzo Chat ID Configurabile
        For any Telegram chat ID configured, all messages should be sent to that specific ID.

        **Feature: another-rss-telegram-bot, Property 2: Utilizzo Chat ID Configurabile**
        **Validates: Requirements 1.2**
        """
        # Act: Mock environment variable and get telegram config
        with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": chat_id}):
            config = Config()
            telegram_config = config.get_telegram_config()

        # Assert: Should return exactly the configured chat ID
        assert telegram_config.chat_id == chat_id

    def test_property_2_empty_chat_id_when_not_configured(self):
        """
        Property 2 edge case: When no chat ID is configured,
        should return empty string as default.

        **Feature: another-rss-telegram-bot, Property 2: Utilizzo Chat ID Configurabile**
        **Validates: Requirements 1.2**
        """
        # Act: No TELEGRAM_CHAT_ID environment variable
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            telegram_config = config.get_telegram_config()

        # Assert: Should return empty string as default
        assert telegram_config.chat_id == ""
