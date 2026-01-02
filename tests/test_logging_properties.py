"""Property-based tests for logging functionality."""

import logging
from datetime import datetime
from io import StringIO
from unittest.mock import Mock, patch

from hypothesis import given
from hypothesis import strategies as st

from src.lambda_handler import lambda_handler
from src.models import FeedItem


class TestLoggingProperties:
    """Property-based tests for logging functionality."""

    @given(
        st.lists(
            st.builds(
                lambda domain: f"https://{domain}.com/feed",
                st.text(
                    alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
                    min_size=3,
                    max_size=20,
                ),
            ),
            min_size=1,
            max_size=2,
        )
    )
    def test_complete_logging_property(self, feed_urls):
        """
        Feature: another-rss-telegram-bot, Property 18: Logging Completo

        For any system execution, there should be logs for start, end, and all
        intermediate steps.
        **Validates: Requirements 8.4, 10.3**
        """
        # Capture all log messages during execution
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        # Get the root logger and configure it
        root_logger = logging.getLogger()
        original_level = root_logger.level
        original_handlers = root_logger.handlers[:]

        # Clear existing handlers and add our capture handler
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

        try:
            # Mock all the dependencies
            with (
                patch("src.lambda_handler.Config") as mock_config_class,
                patch("src.lambda_handler.FeedProcessor") as mock_feed_processor_class,
                patch("src.lambda_handler.Deduplicator") as mock_deduplicator_class,
                patch("src.lambda_handler.Summarizer") as mock_summarizer_class,
                patch(
                    "src.lambda_handler.TelegramPublisher"
                ) as mock_telegram_publisher_class,
                patch("src.lambda_handler.get_telegram_token") as mock_get_token,
                patch("src.lambda_handler.send_cloudwatch_metrics"),
            ):
                # Setup config mock
                mock_config = Mock()
                mock_config.get_feed_urls.return_value = feed_urls
                mock_config.telegram_secret_name = "test-secret"
                mock_config.aws_region = "us-east-1"
                mock_config.dynamodb_table = "test-table"
                mock_config.get_bedrock_config.return_value = Mock()
                mock_config.get_telegram_config.return_value = Mock(bot_token="")
                mock_config_class.return_value = mock_config

                # Setup feed processor mock
                mock_feed_processor = Mock()
                mock_feed_processor_class.return_value = mock_feed_processor

                # Create one mock item per feed
                all_mock_items = []
                for i, feed_url in enumerate(feed_urls):
                    item = FeedItem(
                        title=f"Test Article {i+1}",
                        link=f"{feed_url}/article{i+1}",
                        published=datetime.now(),
                        content=f"Test content {i+1}",
                        feed_url=feed_url,
                        guid=f"guid-{i+1}",
                    )
                    all_mock_items.append(item)

                # Configure feed processor to return items
                def mock_parse_feed(feed_url):
                    return [
                        item for item in all_mock_items if item.feed_url == feed_url
                    ]

                mock_feed_processor.parse_feed.side_effect = mock_parse_feed

                # Setup other mocks
                mock_deduplicator = Mock()
                mock_deduplicator.generate_item_id.return_value = "test-id"
                mock_deduplicator.is_duplicate.return_value = False
                mock_deduplicator.store_item.return_value = None
                mock_deduplicator_class.return_value = mock_deduplicator

                mock_summarizer = Mock()
                mock_summarizer.summarize.return_value = Mock(
                    title="Test Summary",
                    bullets=["Point 1", "Point 2", "Point 3"],
                    why_it_matters="Test importance",
                )
                mock_summarizer_class.return_value = mock_summarizer

                mock_telegram_publisher = Mock()
                mock_telegram_publisher.send_message.return_value = True
                mock_telegram_publisher_class.return_value = mock_telegram_publisher

                mock_get_token.return_value = "test-token"

                # Execute lambda handler
                event = {}
                context = Mock()
                context.aws_request_id = "test-request-123"
                context.function_name = "test-function"

                result = lambda_handler(event, context)

                # Get all log output
                log_output = log_capture.getvalue()

                # Verify execution completed successfully
                assert result["statusCode"] == 200

                # Verify that essential logging steps are present
                # The logs should contain key execution steps regardless of format

                # Check for execution start
                assert (
                    "Starting" in log_output
                ), f"No execution start log found. Output: {log_output}"

                # Check for execution end
                assert (
                    "Completed" in log_output
                    or "execution completed" in log_output.lower()
                ), f"No execution end log found. Output: {log_output}"

                # Check for configuration step
                assert (
                    "Configuration" in log_output or "initialized" in log_output
                ), f"No configuration log found. Output: {log_output}"

                # Check for feed processing logs
                for feed_url in feed_urls:
                    # Should have log mentioning this specific feed
                    assert (
                        feed_url in log_output or "Processing feed" in log_output
                    ), f"No feed processing log found for {feed_url}. Output: {log_output}"

                # Check for metrics logging
                assert (
                    "metrics" in log_output.lower()
                    or "cloudwatch" in log_output.lower()
                ), f"No metrics log found. Output: {log_output}"

                # Verify that timestamps are present (basic check)
                # Look for patterns that suggest structured logging with timestamps
                lines = log_output.split("\n")
                non_empty_lines = [line for line in lines if line.strip()]

                # Should have multiple log lines
                assert (
                    len(non_empty_lines) >= 5
                ), f"Expected at least 5 log lines, got {len(non_empty_lines)}. Output: {log_output}"

                # Verify execution flow is logged
                # Should have logs for different stages of processing
                processing_stages = ["Starting", "Processing", "Completed"]

                for stage in processing_stages:
                    assert any(
                        stage in line for line in non_empty_lines
                    ), f"Missing log for stage '{stage}'. Output: {log_output}"

        finally:
            # Restore original logging configuration
            root_logger.handlers.clear()
            root_logger.handlers.extend(original_handlers)
            root_logger.setLevel(original_level)
            handler.close()
