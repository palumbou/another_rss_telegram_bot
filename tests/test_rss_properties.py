"""Property-based tests for RSS Feed Processor."""

from datetime import datetime
from unittest.mock import Mock

from hypothesis import given
from hypothesis import strategies as st

from src.models import FeedItem
from src.rss import FeedProcessor


class TestFeedProcessorProperties:
    """Property-based tests for FeedProcessor."""

    @given(
        st.text().filter(
            lambda x: not x.startswith("https://")
            and x.strip()
            and "[" not in x
            and "]" not in x
        )
    )
    def test_https_requirement_property(self, non_https_url):
        """
        Feature: another-rss-telegram-bot, Property 3: Download HTTPS Obbligatorio

        For all feed URLs that are not HTTPS, the system should reject them.
        **Validates: Requirements 4.1**
        """
        processor = FeedProcessor()

        # Ensure we have a valid URL format but not HTTPS
        if not non_https_url.startswith(("http://", "ftp://", "file://")):
            test_url = (
                f"http://{non_https_url}" if non_https_url else "http://example.com"
            )
        else:
            test_url = non_https_url

        # Should raise ValueError for non-HTTPS URLs
        try:
            processor.parse_feed(test_url)
            # If no exception is raised, the test should fail
            raise AssertionError(f"Expected ValueError for non-HTTPS URL: {test_url}")
        except ValueError as e:
            # Check if it's our HTTPS error or a URL parsing error
            error_msg = str(e)
            assert (
                "Feed URL must use HTTPS protocol" in error_msg
                or "Invalid IPv6 URL" in error_msg
                or "Invalid URL" in error_msg
            ), f"Unexpected error: {error_msg}"

    @given(
        st.text(min_size=1, max_size=100),  # title
        st.text(min_size=1, max_size=200),  # link
        st.text(min_size=1, max_size=500),  # content
        st.text(min_size=1, max_size=100),  # feed_url
        st.one_of(st.none(), st.text(min_size=1, max_size=50)),  # guid
    )
    def test_field_extraction_completeness_property(
        self, title, link, content, feed_url, guid
    ):
        """
        Feature: another-rss-telegram-bot, Property 4: Estrazione Campi Completa

        For any valid feed item, the normalized output should contain title, link,
        published date and content.
        **Validates: Requirements 4.2**
        """
        processor = FeedProcessor()

        # Create a mock feed entry
        mock_entry = Mock()
        mock_entry.title = title
        mock_entry.link = link
        mock_entry.summary = content
        mock_entry.published = "2024-01-01T10:00:00Z"
        if guid:
            mock_entry.id = guid
        else:
            # Remove id attribute if guid is None
            if hasattr(mock_entry, "id"):
                delattr(mock_entry, "id")

        # Normalize the item
        result = processor.normalize_item(mock_entry, f"https://{feed_url}")

        # Verify all required fields are present and non-empty
        assert isinstance(result, FeedItem)
        assert result.title == title
        assert result.link == link
        assert isinstance(result.published, datetime)
        assert result.content is not None  # Content should be present (may be cleaned)
        assert result.feed_url == f"https://{feed_url}"

        # GUID should match if provided
        if guid:
            assert result.guid == guid

    @given(
        st.text(min_size=1, max_size=500).filter(
            lambda x: x.strip() and not x.startswith("<") and not x.startswith(">")
        )
    )
    def test_html_cleaning_property(self, content_with_html):
        """
        Feature: another-rss-telegram-bot, Property 5: Pulizia HTML

        For any content containing HTML tags, the output should be free of HTML markup.
        **Validates: Requirements 4.3**
        """
        processor = FeedProcessor()

        # Add some HTML tags to the content to ensure we're testing HTML cleaning
        html_content = f"<p>{content_with_html}</p><script>alert('test')</script><style>body{{color:red}}</style>"

        # Clean the HTML content
        result = processor.clean_html_content(html_content)

        # Verify HTML tags are removed
        assert "<" not in result
        assert ">" not in result
        assert "script" not in result.lower()
        assert "style" not in result.lower()

        # Verify the original text content is preserved (at least partially)
        # The content should not be empty since we filtered for non-empty content
        assert result.strip() != ""
