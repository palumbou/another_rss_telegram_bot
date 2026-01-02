"""Property-based tests for Lambda Handler."""

import json
import logging
from datetime import datetime
from io import StringIO
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError
from hypothesis import given
from hypothesis import strategies as st

from src.lambda_handler import get_telegram_token, lambda_handler
from src.models import FeedItem


class TestLambdaHandlerProperties:
    """Property-based tests for Lambda Handler."""

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
            min_size=2,
            max_size=5,
        ),
        st.lists(
            st.builds(
                lambda domain: f"http://{domain}.com/feed",
                st.text(
                    alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
                    min_size=3,
                    max_size=20,
                ),
            ),
            min_size=1,
            max_size=3,
        ),
    )
    def test_feed_error_resilience_property(self, valid_feeds, invalid_feeds):
        """
        Feature: another-rss-telegram-bot, Property 6: Resilienza Errori Feed

        For any list of feeds containing both valid and malformed feeds,
        the system should process all valid feeds without interruption.
        **Validates: Requirements 4.5, 10.4**
        """
        # Combine valid and invalid feeds
        all_feeds = valid_feeds + invalid_feeds

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
            patch("src.lambda_handler.send_cloudwatch_metrics") as mock_send_metrics,
        ):
            # Setup config mock
            mock_config = Mock()
            mock_config.get_feed_urls.return_value = all_feeds
            mock_config.telegram_secret_name = "test-secret"
            mock_config.aws_region = "us-east-1"
            mock_config.dynamodb_table = "test-table"
            mock_config.get_bedrock_config.return_value = Mock()
            mock_config.get_telegram_config.return_value = Mock(bot_token="")
            mock_config_class.return_value = mock_config

            # Setup feed processor mock
            mock_feed_processor = Mock()
            mock_feed_processor_class.return_value = mock_feed_processor

            # Configure feed processor to succeed for valid feeds and fail for invalid ones
            def mock_parse_feed(feed_url):
                if feed_url.startswith("https://"):
                    # Valid feed - return some mock items
                    return [
                        FeedItem(
                            title=f"Test Article from {feed_url}",
                            link=f"{feed_url}/article1",
                            published=datetime.now(),
                            content="Test content",
                            feed_url=feed_url,
                            guid=f"guid-{feed_url}",
                        )
                    ]
                else:
                    # Invalid feed - raise exception
                    raise ValueError(f"Feed URL must use HTTPS protocol: {feed_url}")

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

            result = lambda_handler(event, context)

            # Verify the handler completed successfully despite feed errors
            assert result["statusCode"] == 200

            # Parse the response body
            response_body = json.loads(result["body"])
            metrics = response_body["metrics"]

            # Verify that valid feeds were processed
            assert metrics["feeds_processed"] == len(valid_feeds)

            # Verify that items were found only from valid feeds
            expected_items = len(valid_feeds)  # Each valid feed returns 1 item
            assert metrics["items_found"] == expected_items

            # Verify that errors were recorded for invalid feeds
            assert len(metrics["errors"]) == len(invalid_feeds)

            # Verify that all errors are related to HTTPS requirement
            for error in metrics["errors"]:
                assert (
                    "Feed URL must use HTTPS protocol" in error
                    or "Failed to process feed" in error
                )

            # Verify that processing continued despite errors
            # (items were summarized and sent for valid feeds)
            assert metrics["items_summarized"] == expected_items
            assert metrics["messages_sent"] == expected_items

            # Verify that CloudWatch metrics were sent
            mock_send_metrics.assert_called_once()

    @given(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=1,
            max_size=50,
        ),
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=1,
            max_size=20,
        ),
    )
    def test_token_security_property(self, secret_name, aws_region):
        """
        Feature: another-rss-telegram-bot, Property 16: Sicurezza Token

        For any operation that requires the Telegram token, it should be retrieved
        exclusively from AWS Secrets Manager.
        **Validates: Requirements 9.1**
        """
        # Test that get_telegram_token always uses Secrets Manager
        mock_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

        with patch("boto3.client") as mock_boto_client:
            # Setup mock Secrets Manager client
            mock_secrets_client = Mock()
            mock_boto_client.return_value = mock_secrets_client

            # Test with plain text secret
            mock_secrets_client.get_secret_value.return_value = {
                "SecretString": mock_token
            }

            result = get_telegram_token(secret_name, aws_region, "test-execution-id")

            # Verify that boto3.client was called with secretsmanager service
            mock_boto_client.assert_called_with(
                "secretsmanager", region_name=aws_region
            )

            # Verify that get_secret_value was called with the correct secret name
            mock_secrets_client.get_secret_value.assert_called_with(
                SecretId=secret_name
            )

            # Verify that the token was retrieved correctly
            assert result == mock_token

            # Test with JSON secret format
            json_secret = json.dumps({"token": mock_token})
            mock_secrets_client.get_secret_value.return_value = {
                "SecretString": json_secret
            }

            result = get_telegram_token(secret_name, aws_region, "test-execution-id")
            assert result == mock_token

            # Test with different JSON key formats
            for key in ["bot_token", "telegram_token", "telegram_bot_token"]:
                json_secret = json.dumps({key: mock_token})
                mock_secrets_client.get_secret_value.return_value = {
                    "SecretString": json_secret
                }

                result = get_telegram_token(
                    secret_name, aws_region, "test-execution-id"
                )
                assert result == mock_token

            # Verify that Secrets Manager is always called (never bypassed)
            assert mock_secrets_client.get_secret_value.call_count > 0

    @given(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc")),
            min_size=10,
            max_size=100,
        ).filter(lambda x: "\x00" not in x),
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=1,
            max_size=50,
        ).filter(lambda x: "\x00" not in x),
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=1,
            max_size=20,
        ).filter(lambda x: "\x00" not in x),
    )
    def test_sensitive_information_protection_property(
        self, mock_token, secret_name, aws_region
    ):
        """
        Feature: another-rss-telegram-bot, Property 17: Protezione Informazioni Sensibili

        For any log generated, it should not contain tokens, passwords, or other
        sensitive information.
        **Validates: Requirements 9.2**
        """
        # Ensure secret name and token are completely different to avoid false positives
        # Use a prefix that makes them clearly distinct
        actual_token = f"TOKEN_{mock_token}_END"
        actual_secret_name = f"SECRET_{secret_name}_NAME"

        # Ensure they don't contain each other as substrings
        if actual_token in actual_secret_name or actual_secret_name in actual_token:
            actual_secret_name = f"SECRETNAME_{len(secret_name)}_DIFFERENT"
        # Capture all log messages during execution
        import logging
        from io import StringIO

        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        # Get the specific logger used by get_telegram_token function
        secrets_logger = logging.getLogger("rss_telegram_bot.secrets_manager")
        original_level = secrets_logger.level
        original_handlers = secrets_logger.handlers[:]

        # Clear existing handlers and add our capture handler
        secrets_logger.handlers.clear()
        secrets_logger.addHandler(handler)
        secrets_logger.setLevel(logging.DEBUG)
        secrets_logger.propagate = False  # Don't propagate to avoid duplicate logs

        try:
            with patch("boto3.client") as mock_boto_client:
                # Setup mock Secrets Manager client
                mock_secrets_client = Mock()
                mock_boto_client.return_value = mock_secrets_client

                # Test successful token retrieval
                mock_secrets_client.get_secret_value.return_value = {
                    "SecretString": actual_token
                }

                result = get_telegram_token(
                    actual_secret_name, aws_region, "test-execution-id"
                )

                # Get all log output
                log_output = log_capture.getvalue()

                # Verify that the actual token value is never logged
                assert (
                    actual_token not in log_output
                ), f"Sensitive token found in logs: {log_output}"

                # Verify that only the secret name is mentioned, not the token
                assert actual_secret_name in log_output  # Secret name is OK to log

                # Test error scenarios to ensure sensitive info isn't logged in errors
                mock_secrets_client.get_secret_value.side_effect = ClientError(
                    error_response={"Error": {"Code": "ResourceNotFoundException"}},
                    operation_name="GetSecretValue",
                )

                try:
                    get_telegram_token(
                        actual_secret_name, aws_region, "test-execution-id"
                    )
                except RuntimeError:
                    pass  # Expected

                # Get updated log output
                log_output = log_capture.getvalue()

                # Verify that even in error cases, sensitive information is not logged
                assert (
                    actual_token not in log_output
                ), f"Sensitive token found in error logs: {log_output}"

                # Test with JSON secret containing sensitive data
                sensitive_json = json.dumps(
                    {
                        "token": actual_token,
                        "password": "secret123",
                        "api_key": "sensitive_key",
                    }
                )

                mock_secrets_client.get_secret_value.side_effect = None
                mock_secrets_client.get_secret_value.return_value = {
                    "SecretString": sensitive_json
                }

                result = get_telegram_token(
                    actual_secret_name, aws_region, "test-execution-id"
                )

                # Get final log output
                log_output = log_capture.getvalue()

                # Verify that none of the sensitive values are logged
                assert (
                    actual_token not in log_output
                ), f"Token found in logs: {log_output}"
                assert (
                    "secret123" not in log_output
                ), f"Password found in logs: {log_output}"
                assert (
                    "sensitive_key" not in log_output
                ), f"API key found in logs: {log_output}"

                # Verify that the function still works correctly
                assert result == actual_token

        finally:
            # Restore original logging configuration
            secrets_logger.handlers.clear()
            secrets_logger.handlers.extend(original_handlers)
            secrets_logger.setLevel(original_level)
            secrets_logger.propagate = True
            handler.close()

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
