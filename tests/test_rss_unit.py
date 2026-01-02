"""Unit tests for RSS Feed Processor specific formats."""

from datetime import datetime
from unittest.mock import Mock

from src.models import FeedItem
from src.rss import FeedProcessor


class TestFeedProcessorUnit:
    """Unit tests for specific RSS/Atom feed formats."""

    def test_rss_2_0_parsing(self):
        """Test parsing RSS 2.0 format with specific example.

        **Validates: Requirements 4.4**
        """
        processor = FeedProcessor()

        # Mock RSS 2.0 entry
        mock_entry = Mock()
        mock_entry.title = "AWS Announces New Service"
        mock_entry.link = "https://aws.amazon.com/blogs/aws/new-service/"
        mock_entry.summary = "<p>AWS has announced a new service for developers.</p>"
        mock_entry.published = "Mon, 01 Jan 2024 10:00:00 GMT"
        mock_entry.guid = "https://aws.amazon.com/blogs/aws/new-service/"

        # Set attributes that might not exist in RSS 2.0 to None
        mock_entry.id = None
        mock_entry.description = None
        mock_entry.content = None

        result = processor.normalize_item(
            mock_entry, "https://aws.amazon.com/blogs/aws/feed/"
        )

        assert isinstance(result, FeedItem)
        assert result.title == "AWS Announces New Service"
        assert result.link == "https://aws.amazon.com/blogs/aws/new-service/"
        assert (
            result.content == "AWS has announced a new service for developers."
        )  # HTML cleaned
        assert result.feed_url == "https://aws.amazon.com/blogs/aws/feed/"
        assert result.guid == "https://aws.amazon.com/blogs/aws/new-service/"
        assert isinstance(result.published, datetime)

    def test_atom_1_0_parsing(self):
        """Test parsing Atom 1.0 format with specific example.

        **Validates: Requirements 4.4**
        """
        processor = FeedProcessor()

        # Mock Atom 1.0 entry
        mock_entry = Mock()
        mock_entry.title = "Security Best Practices Update"
        mock_entry.link = "https://aws.amazon.com/blogs/security/best-practices-update/"
        mock_entry.id = "tag:aws.amazon.com,2024:/blogs/security/best-practices-update"
        mock_entry.published = "2024-01-01T10:00:00Z"

        # Atom feeds use content instead of summary
        mock_content = Mock()
        mock_content.get.return_value = "<div><h2>Important Update</h2><p>New security guidelines available.</p></div>"
        mock_entry.content = [mock_content]

        # Set RSS-specific attributes to None for Atom
        mock_entry.summary = None
        mock_entry.description = None
        mock_entry.guid = None

        result = processor.normalize_item(
            mock_entry, "https://aws.amazon.com/blogs/security/feed/"
        )

        assert isinstance(result, FeedItem)
        assert result.title == "Security Best Practices Update"
        assert (
            result.link
            == "https://aws.amazon.com/blogs/security/best-practices-update/"
        )
        assert "Important Update" in result.content
        assert "New security guidelines available." in result.content
        assert "<h2>" not in result.content  # HTML should be cleaned
        assert result.feed_url == "https://aws.amazon.com/blogs/security/feed/"
        assert (
            result.guid
            == "tag:aws.amazon.com,2024:/blogs/security/best-practices-update"
        )
        assert isinstance(result.published, datetime)

    def test_feed_with_missing_fields(self):
        """Test handling of feed entries with missing optional fields."""
        processor = FeedProcessor()

        # Mock entry with minimal fields
        mock_entry = Mock()
        mock_entry.title = "Minimal Entry"
        mock_entry.link = "https://example.com/minimal"

        # Set optional fields to None
        mock_entry.summary = None
        mock_entry.description = None
        mock_entry.content = None
        mock_entry.published = None
        mock_entry.id = None
        mock_entry.guid = None

        result = processor.normalize_item(mock_entry, "https://example.com/feed/")

        assert isinstance(result, FeedItem)
        assert result.title == "Minimal Entry"
        assert result.link == "https://example.com/minimal"
        assert result.content == ""  # Should be empty string, not None
        assert result.feed_url == "https://example.com/feed/"
        assert result.guid is None
        assert isinstance(result.published, datetime)  # Should default to current time

    def test_html_cleaning_specific_cases(self):
        """Test HTML cleaning with specific problematic cases."""
        processor = FeedProcessor()

        # Test various HTML scenarios
        test_cases = [
            ("<p>Simple paragraph</p>", "Simple paragraph"),
            ("<div><h1>Title</h1><p>Content</p></div>", "Title Content"),
            ("<script>alert('xss')</script><p>Safe content</p>", "Safe content"),
            ("<style>body{color:red}</style><p>Styled content</p>", "Styled content"),
            ("Plain text without HTML", "Plain text without HTML"),
            ("<p>Multiple  \n\n  spaces   and\tlines</p>", "Multiple spaces and lines"),
        ]

        for html_input, expected_output in test_cases:
            result = processor.clean_html_content(html_input)
            assert result == expected_output, f"Failed for input: {html_input}"

    def test_empty_and_none_content_handling(self):
        """Test handling of empty or None content."""
        processor = FeedProcessor()

        # Test empty content
        assert processor.clean_html_content("") == ""
        assert processor.clean_html_content(None) == ""
        assert processor.clean_html_content("   ") == ""

        # Test content with only HTML tags
        assert processor.clean_html_content("<div></div>") == ""
        assert processor.clean_html_content("<p><br/></p>") == ""
