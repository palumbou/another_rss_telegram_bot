"""Property-based tests for Summarizer."""

from datetime import datetime
from unittest.mock import Mock, patch

from hypothesis import given
from hypothesis import strategies as st

from src.config import BedrockConfig
from src.models import FeedItem, Summary
from src.summarize import Summarizer


class TestSummarizerProperties:
    """Property-based tests for Summarizer."""

    @given(
        st.text(
            alphabet=st.characters(
                whitelist_categories=(
                    "Lu",
                    "Ll",
                    "Nd",
                    "Pc",
                    "Pd",
                    "Ps",
                    "Pe",
                    "Po",
                    "Zs",
                )
            ),
            min_size=50,
            max_size=500,
        )
    )
    def test_summary_format_consistency_property(self, content):
        """
        Feature: another-rss-telegram-bot, Property 11: Formato Riassunto Consistente

        For any summary generated, it should contain exactly: 1 title, 3 bullet points
        (≤15 words each), 1 "Perché conta:" line (≤20 words).
        **Validates: Requirements 6.2**
        """
        # Create a mock Bedrock config
        config = BedrockConfig()

        # Create summarizer with mocked Bedrock client to avoid AWS calls
        with patch("boto3.client"):
            summarizer = Summarizer(config)
            summarizer.bedrock_client = (
                None  # Force fallback to extractive summarization
            )

            # Create a test feed item
            feed_item = FeedItem(
                title="Test Article",
                link="https://example.com/test",
                published=datetime.now(),
                content=content,
                feed_url="https://example.com/feed",
            )

            # Generate summary
            result = summarizer.summarize(feed_item)

            # Verify the result is a Summary object
            assert isinstance(result, Summary)

            # Verify title is present and within word limit (10 words max)
            assert result.title is not None
            assert len(result.title.strip()) > 0
            title_words = result.title.split()
            assert (
                len(title_words) <= 10
            ), f"Title has {len(title_words)} words, max is 10"

            # Verify exactly 3 bullet points
            assert isinstance(result.bullets, list)
            assert (
                len(result.bullets) == 3
            ), f"Expected 3 bullets, got {len(result.bullets)}"

            # Verify each bullet point is within word limit (15 words max)
            for i, bullet in enumerate(result.bullets):
                assert bullet is not None
                assert len(bullet.strip()) > 0
                bullet_words = bullet.split()
                assert (
                    len(bullet_words) <= 15
                ), f"Bullet {i+1} has {len(bullet_words)} words, max is 15"

            # Verify "Perché conta" line is present and within word limit (20 words max)
            assert result.why_it_matters is not None
            assert len(result.why_it_matters.strip()) > 0
            why_words = result.why_it_matters.split()
            assert (
                len(why_words) <= 20
            ), f"'Perché conta' has {len(why_words)} words, max is 20"

    @given(
        st.text(
            alphabet=st.characters(
                whitelist_categories=(
                    "Lu",
                    "Ll",
                    "Nd",
                    "Pc",
                    "Pd",
                    "Ps",
                    "Pe",
                    "Po",
                    "Zs",
                )
            ),
            min_size=100,
            max_size=1000,
        )
    )
    def test_bedrock_fallback_property(self, content):
        """
        Feature: another-rss-telegram-bot, Property 12: Fallback Summarizer

        For any Bedrock error (AccessDenied or unavailability), the system should use
        the fallback extractive summarization method.
        **Validates: Requirements 6.3**
        """
        # Create a mock Bedrock config
        config = BedrockConfig()

        # Test case 1: No Bedrock client (initialization failed)
        with patch("boto3.client"):
            summarizer = Summarizer(config)
            summarizer.bedrock_client = None  # Simulate initialization failure

            feed_item = FeedItem(
                title="Test Article",
                link="https://example.com/test",
                published=datetime.now(),
                content=content,
                feed_url="https://example.com/feed",
            )

            # Should use fallback and still produce valid summary
            result = summarizer.summarize(feed_item)
            assert isinstance(result, Summary)
            assert len(result.bullets) == 3
            assert result.title is not None
            assert result.why_it_matters is not None

        # Test case 2: Bedrock client exists but returns AccessDenied
        with patch("boto3.client") as mock_boto_client:
            mock_client = Mock()
            mock_boto_client.return_value = mock_client

            # Mock AccessDenied error
            from botocore.exceptions import ClientError

            error_response = {"Error": {"Code": "AccessDeniedException"}}
            mock_client.invoke_model.side_effect = ClientError(
                error_response, "InvokeModel"
            )

            summarizer = Summarizer(config)

            feed_item = FeedItem(
                title="Test Article",
                link="https://example.com/test",
                published=datetime.now(),
                content=content,
                feed_url="https://example.com/feed",
            )

            # Should catch the error and use fallback
            result = summarizer.summarize(feed_item)
            assert isinstance(result, Summary)
            assert len(result.bullets) == 3
            assert result.title is not None
            assert result.why_it_matters is not None

        # Test case 3: Bedrock client exists but returns empty response
        with patch("boto3.client") as mock_boto_client:
            mock_client = Mock()
            mock_boto_client.return_value = mock_client

            # Mock empty response
            mock_response = {"body": Mock()}
            mock_response["body"].read.return_value = '{"content": []}'
            mock_client.invoke_model.return_value = mock_response

            summarizer = Summarizer(config)

            feed_item = FeedItem(
                title="Test Article",
                link="https://example.com/test",
                published=datetime.now(),
                content=content,
                feed_url="https://example.com/feed",
            )

            # Should detect empty response and use fallback
            result = summarizer.summarize(feed_item)
            assert isinstance(result, Summary)
            assert len(result.bullets) == 3
            assert result.title is not None
            assert result.why_it_matters is not None
