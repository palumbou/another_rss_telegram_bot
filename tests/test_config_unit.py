"""Unit tests for configuration management."""

import os
from unittest.mock import patch

from src.config import Config


class TestConfigUnit:
    """Unit tests for Config class."""

    def test_default_aws_feeds_presence(self):
        """
        Test that default AWS feeds include required URLs.
        Verifies presence of AWS Blog, What's New, and Security feeds.

        Requirements: 11.1, 11.2, 11.3
        """
        # Arrange
        config = Config()

        # Act
        default_feeds = config.DEFAULT_AWS_FEEDS

        # Assert: Check for required AWS feeds
        # Requirement 11.1: AWS Blog feed
        aws_blog_feed = "https://aws.amazon.com/blogs/aws/feed/"
        assert (
            aws_blog_feed in default_feeds
        ), f"AWS Blog feed {aws_blog_feed} not found in default feeds"

        # Requirement 11.2: AWS What's New feed
        whats_new_feed = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"
        assert (
            whats_new_feed in default_feeds
        ), f"AWS What's New feed {whats_new_feed} not found in default feeds"

        # Requirement 11.3: AWS Security Blog feed
        security_feed = "https://aws.amazon.com/blogs/security/feed/"
        assert (
            security_feed in default_feeds
        ), f"AWS Security Blog feed {security_feed} not found in default feeds"

        # Verify feeds are not empty
        assert len(default_feeds) > 0, "Default feeds list should not be empty"

        # Verify all feeds are HTTPS URLs
        for feed_url in default_feeds:
            assert feed_url.startswith(
                "https://"
            ), f"Feed URL {feed_url} should use HTTPS protocol"

    def test_get_feed_urls_returns_defaults_when_no_env_var(self):
        """
        Test that get_feed_urls returns default AWS feeds when no environment variable is set.

        Requirements: 11.1, 11.2, 11.3
        """
        # Arrange & Act: Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            feed_urls = config.get_feed_urls()

        # Assert: Should return default feeds including required AWS feeds
        assert feed_urls == config.DEFAULT_AWS_FEEDS

        # Verify specific required feeds are present
        assert "https://aws.amazon.com/blogs/aws/feed/" in feed_urls
        assert "https://aws.amazon.com/about-aws/whats-new/recent/feed/" in feed_urls
        assert "https://aws.amazon.com/blogs/security/feed/" in feed_urls

    def test_default_feeds_are_valid_urls(self):
        """
        Test that all default AWS feeds are valid HTTPS URLs.

        Requirements: 11.1, 11.2, 11.3
        """
        # Arrange
        config = Config()

        # Act
        default_feeds = config.DEFAULT_AWS_FEEDS

        # Assert: All feeds should be valid HTTPS URLs
        for feed_url in default_feeds:
            assert isinstance(
                feed_url, str
            ), f"Feed URL should be string, got {type(feed_url)}"
            assert (
                feed_url.strip() == feed_url
            ), f"Feed URL should not have leading/trailing whitespace: '{feed_url}'"
            assert feed_url.startswith(
                "https://"
            ), f"Feed URL should use HTTPS: {feed_url}"
            assert (
                "aws.amazon.com" in feed_url
            ), f"Feed URL should be from AWS domain: {feed_url}"
            assert feed_url.endswith(
                "/feed/"
            ), f"Feed URL should end with /feed/: {feed_url}"
