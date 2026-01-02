"""Property-based tests for Deduplicator."""

from datetime import datetime
from unittest.mock import Mock, patch

from hypothesis import given
from hypothesis import strategies as st

from src.dedup import Deduplicator
from src.models import FeedItem


class TestDeduplicatorProperties:
    """Property-based tests for Deduplicator."""

    @given(
        st.text(min_size=1, max_size=100),  # title
        st.text(min_size=1, max_size=200),  # link
        st.text(min_size=1, max_size=500),  # content
        st.text(min_size=1, max_size=100),  # feed_url
        st.text(min_size=1, max_size=50),  # guid (non-empty)
    )
    def test_guid_based_id_generation_property(
        self, title, link, content, feed_url, guid
    ):
        """
        Feature: another-rss-telegram-bot, Property 7: Utilizzo GUID per Deduplicazione

        For any feed item with GUID present, the unique identifier should be based on the GUID.
        **Validates: Requirements 5.1**
        """
        # Create a mock DynamoDB setup to avoid actual AWS calls
        with patch("boto3.resource"):
            deduplicator = Deduplicator("test-table", "us-east-1")

            # Create feed item with GUID
            feed_item = FeedItem(
                title=title,
                link=link,
                published=datetime.now(),
                content=content,
                feed_url=feed_url,
                guid=guid,
            )

            # Generate ID
            result_id = deduplicator.generate_item_id(feed_item)

            # Verify that the ID is exactly the GUID when GUID is present
            assert result_id == guid
            assert result_id is not None
            assert len(result_id) > 0

    @given(
        st.text(min_size=1, max_size=100),  # title
        st.text(min_size=1, max_size=200),  # link
        st.text(min_size=1, max_size=500),  # content
        st.text(min_size=1, max_size=100),  # feed_url
    )
    def test_hash_fallback_id_generation_property(self, title, link, content, feed_url):
        """
        Feature: another-rss-telegram-bot, Property 8: Hash Fallback per Deduplicazione

        For any feed item without GUID, the unique identifier should be a SHA256 hash
        of feed_url + link + published_date.
        **Validates: Requirements 5.2**
        """
        import hashlib

        # Create a mock DynamoDB setup to avoid actual AWS calls
        with patch("boto3.resource"):
            deduplicator = Deduplicator("test-table", "us-east-1")

            # Create feed item without GUID (guid=None)
            published_time = datetime.now()
            feed_item = FeedItem(
                title=title,
                link=link,
                published=published_time,
                content=content,
                feed_url=feed_url,
                guid=None,  # No GUID, should use hash fallback
            )

            # Generate ID
            result_id = deduplicator.generate_item_id(feed_item)

            # Calculate expected hash
            hash_input = f"{feed_url}{link}{published_time.isoformat()}"
            expected_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

            # Verify that the ID is the expected SHA256 hash
            assert result_id == expected_hash
            assert len(result_id) == 64  # SHA256 hash length
            assert all(c in "0123456789abcdef" for c in result_id)  # Valid hex string

    @given(
        st.text(min_size=1, max_size=100),  # title
        st.text(min_size=1, max_size=200),  # link
        st.text(min_size=1, max_size=500),  # content
        st.text(min_size=1, max_size=100),  # feed_url
        st.one_of(st.none(), st.text(min_size=1, max_size=50)),  # guid (optional)
    )
    def test_duplicate_prevention_property(self, title, link, content, feed_url, guid):
        """
        Feature: another-rss-telegram-bot, Property 9: Prevenzione Duplicati

        For any item already present in DynamoDB, the system should skip processing.
        **Validates: Requirements 5.3, 5.4**
        """
        # Create a mock DynamoDB setup
        with patch("boto3.resource") as mock_resource:
            mock_table = Mock()
            mock_resource.return_value.Table.return_value = mock_table

            deduplicator = Deduplicator("test-table", "us-east-1")

            # Create feed item
            feed_item = FeedItem(
                title=title,
                link=link,
                published=datetime.now(),
                content=content,
                feed_url=feed_url,
                guid=guid,
            )

            # Generate ID for the item
            item_id = deduplicator.generate_item_id(feed_item)

            # Test case 1: Item doesn't exist (not a duplicate)
            mock_table.get_item.return_value = {}  # No 'Item' key means not found
            assert deduplicator.is_duplicate(item_id) is False

            # Test case 2: Item exists (is a duplicate)
            mock_table.get_item.return_value = {"Item": {"item_id": item_id}}
            assert deduplicator.is_duplicate(item_id) is True

            # Verify that get_item was called with correct parameters
            expected_calls = [
                {"Key": {"item_id": item_id}},
                {"Key": {"item_id": item_id}},
            ]
            actual_calls = [call[1] for call in mock_table.get_item.call_args_list]
            assert actual_calls == expected_calls

    @given(
        st.text(min_size=1, max_size=100),  # title
        st.text(min_size=1, max_size=200),  # link
        st.text(min_size=1, max_size=500),  # content
        st.text(min_size=1, max_size=100),  # feed_url
        st.one_of(st.none(), st.text(min_size=1, max_size=50)),  # guid (optional)
    )
    def test_storage_with_ttl_property(self, title, link, content, feed_url, guid):
        """
        Feature: another-rss-telegram-bot, Property 10: Storage con TTL

        For any new item processed, it should be stored in DynamoDB with TTL of 90 days.
        **Validates: Requirements 5.5**
        """
        from datetime import timedelta

        # Create a mock DynamoDB setup
        with patch("boto3.resource") as mock_resource:
            mock_table = Mock()
            mock_resource.return_value.Table.return_value = mock_table

            deduplicator = Deduplicator("test-table", "us-east-1")

            # Create feed item
            feed_item = FeedItem(
                title=title,
                link=link,
                published=datetime.now(),
                content=content,
                feed_url=feed_url,
                guid=guid,
            )

            # Generate ID for the item
            item_id = deduplicator.generate_item_id(feed_item)

            # Store the item
            with patch("src.dedup.datetime") as mock_datetime:
                # Mock datetime.now() to have a predictable time
                mock_now = datetime(2024, 1, 1, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

                deduplicator.store_item(item_id, feed_item)

                # Verify put_item was called
                assert mock_table.put_item.called

                # Get the call arguments
                call_args = mock_table.put_item.call_args[1]
                stored_item = call_args["Item"]

                # Verify the stored item structure
                assert stored_item["item_id"] == item_id
                assert stored_item["feed_url"] == feed_url
                assert stored_item["link"] == link
                assert stored_item["title"] == title
                assert "processed_at" in stored_item
                assert "ttl" in stored_item

                # Verify TTL is approximately 90 days from now
                expected_ttl = int((mock_now + timedelta(days=90)).timestamp())
                actual_ttl = stored_item["ttl"]

                # Allow for small differences due to timing
                assert abs(actual_ttl - expected_ttl) <= 1  # Within 1 second tolerance
