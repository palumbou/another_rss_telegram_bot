"""Main Lambda handler for RSS Telegram Bot."""

import json
import os
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .config import Config
from .dedup import Deduplicator
from .logging_config import create_execution_logger, setup_structured_logging
from .rss import FeedProcessor
from .summarize import Summarizer
from .telegram import TelegramPublisher

# Setup structured logging
setup_structured_logging(os.getenv("LOG_LEVEL", "INFO"))


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler that orchestrates the RSS-to-Telegram pipeline.

    Args:
        event: Lambda event data
        context: Lambda context object

    Returns:
        Response dictionary with status and metrics
    """
    # Create execution logger with unique ID
    execution_id = f"lambda_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')}"
    main_logger = create_execution_logger("main", execution_id)

    # Log execution start
    main_logger.log_execution_start(
        lambda_request_id=getattr(context, "aws_request_id", "unknown"),
        lambda_function_name=getattr(context, "function_name", "unknown"),
    )

    # Initialize metrics
    metrics = {
        "feeds_processed": 0,
        "items_found": 0,
        "items_deduplicated": 0,
        "items_summarized": 0,
        "messages_sent": 0,
        "errors": [],
    }

    try:
        # Initialize configuration
        config = Config()
        main_logger.info("Configuration initialized")

        # Get feed URLs
        feed_urls = config.get_feed_urls()
        main_logger.info(
            f"Processing {len(feed_urls)} feeds", feed_count=len(feed_urls)
        )

        # Initialize components with structured logging
        feed_processor = FeedProcessor(execution_id=execution_id)
        deduplicator = Deduplicator(
            table_name=config.dynamodb_table,
            aws_region=config.aws_region,
            execution_id=execution_id,
        )
        summarizer = Summarizer(config.get_bedrock_config(), execution_id=execution_id)

        # Get Telegram token from Secrets Manager
        telegram_config = config.get_telegram_config()
        telegram_token = get_telegram_token(
            config.telegram_secret_name, config.aws_region, execution_id
        )

        # Basic validation - ensure token is not empty
        if not telegram_token or not telegram_token.strip():
            raise ValueError("Telegram bot configuration cannot be empty")

        telegram_config.bot_token = telegram_token

        telegram_publisher = TelegramPublisher(
            telegram_config, execution_id=execution_id
        )

        # Process each feed
        all_items = []
        for feed_url in feed_urls:
            try:
                main_logger.info(f"Processing feed: {feed_url}", feed_url=feed_url)
                items = feed_processor.parse_feed(feed_url)
                all_items.extend(items)
                metrics["feeds_processed"] += 1
                main_logger.log_feed_processing(feed_url, len(items))
            except Exception as e:
                error_msg = f"Failed to process feed {feed_url}: {str(e)}"
                main_logger.error(error_msg, feed_url=feed_url, error=str(e))
                metrics["errors"].append(error_msg)
                # Continue with other feeds (Requirement 4.5, 10.4)
                continue

        metrics["items_found"] = len(all_items)
        main_logger.info(
            f"Total items found: {len(all_items)}", total_items=len(all_items)
        )

        # Process items through the pipeline
        for item in all_items:
            try:
                # Generate unique ID for deduplication
                item_id = deduplicator.generate_item_id(item)

                # Check for duplicates
                if deduplicator.is_duplicate(item_id):
                    main_logger.log_item_processing(item.title, "skipped_duplicate")
                    metrics["items_deduplicated"] += 1
                    continue

                # Store item to prevent future duplicates
                deduplicator.store_item(item_id, item)

                # Generate summary
                summary = summarizer.summarize(item)
                metrics["items_summarized"] += 1
                main_logger.log_item_processing(item.title, "summarized")

                # Send to Telegram
                success = telegram_publisher.send_message(summary, item.link, item.feed_url)
                if success:
                    metrics["messages_sent"] += 1
                    main_logger.log_item_processing(item.title, "sent_to_telegram")
                else:
                    error_msg = f"Failed to send message for: {item.title}"
                    main_logger.error(error_msg, item_title=item.title)
                    metrics["errors"].append(error_msg)

            except Exception as e:
                error_msg = f"Failed to process item '{item.title}': {str(e)}"
                main_logger.error(error_msg, item_title=item.title, error=str(e))
                metrics["errors"].append(error_msg)
                # Continue with other items (Requirement 10.4)
                continue

        # Log final metrics
        main_logger.log_metrics(metrics)

        # Send custom CloudWatch metrics
        send_cloudwatch_metrics(metrics, config.aws_region, execution_id)

        # Log successful execution end
        main_logger.log_execution_end(success=True, metrics=metrics)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "RSS Telegram Bot execution completed",
                    "execution_id": execution_id,
                    "metrics": metrics,
                }
            ),
        }

    except Exception as e:
        error_msg = f"Critical error in Lambda handler: {str(e)}"
        main_logger.error(error_msg, error=str(e))
        metrics["errors"].append(error_msg)

        # Send error metrics
        send_cloudwatch_metrics(
            metrics,
            config.aws_region if "config" in locals() else "us-east-1",
            execution_id,
        )

        # Log failed execution end
        main_logger.log_execution_end(success=False, metrics=metrics, error=error_msg)

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "RSS Telegram Bot execution failed",
                    "execution_id": execution_id,
                    "error": error_msg,
                    "metrics": metrics,
                }
            ),
        }


def get_telegram_token(secret_name: str, aws_region: str, execution_id: str) -> str:
    """
    Retrieve Telegram bot configuration from AWS Secrets Manager.

    This function securely retrieves the Telegram bot configuration from AWS Secrets Manager,
    supporting both plain string and JSON secret formats. It never logs sensitive
    information and follows security best practices.

    Args:
        secret_name: Name of the secret in Secrets Manager
        aws_region: AWS region for Secrets Manager client
        execution_id: Execution ID for logging context

    Returns:
        Telegram bot configuration value

    Raises:
        ClientError: If secret cannot be retrieved from Secrets Manager
        ValueError: If secret format is invalid or configuration is empty
    """
    secrets_logger = create_execution_logger("secrets_manager", execution_id)

    if not secret_name or not secret_name.strip():
        raise ValueError("Secret name cannot be empty")

    if not aws_region or not aws_region.strip():
        raise ValueError("AWS region cannot be empty")

    try:
        secrets_logger.info(
            f"Retrieving Telegram configuration from Secrets Manager: {secret_name}"
        )
        secrets_client = boto3.client("secretsmanager", region_name=aws_region)

        response = secrets_client.get_secret_value(SecretId=secret_name)

        if "SecretString" not in response:
            raise ValueError(f"Secret {secret_name} does not contain a string value")

        secret_value = response["SecretString"]

        if not secret_value or not secret_value.strip():
            raise ValueError(f"Secret {secret_name} contains empty value")

        # Handle both string and JSON secret formats
        try:
            # Try to parse as JSON first
            secret_data = json.loads(secret_value)
            if isinstance(secret_data, dict):
                # Look for common configuration field names
                for key in [
                    "token",
                    "bot_token",
                    "telegram_token",
                    "telegram_bot_token",
                ]:
                    if key in secret_data:
                        config_value = secret_data[key]
                        if config_value and config_value.strip():
                            secrets_logger.info(
                                "Successfully retrieved configuration from JSON secret"
                            )
                            return config_value.strip()

                # If no expected key found, try to use the first non-empty value
                for value in secret_data.values():
                    if isinstance(value, str) and value.strip():
                        secrets_logger.info(
                            "Using first available value from JSON secret"
                        )
                        return value.strip()

                raise ValueError(
                    f"No valid configuration found in JSON secret {secret_name}"
                )
            else:
                raise ValueError(f"JSON secret {secret_name} must be an object")

        except json.JSONDecodeError:
            # Not JSON, use as plain string
            config_value = secret_value.strip()
            if not config_value:
                raise ValueError(f"Plain text secret {secret_name} is empty")

            secrets_logger.info(
                "Successfully retrieved configuration from plain text secret"
            )
            return config_value

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        secrets_logger.error(
            f"AWS Secrets Manager error retrieving {secret_name}: {error_code}"
        )
        raise RuntimeError(f"Failed to retrieve secret {secret_name}") from e
    except ValueError as e:
        secrets_logger.error(f"Invalid secret format for {secret_name}: {e}")
        raise RuntimeError(f"Invalid secret format for {secret_name}") from e
    except Exception as e:
        secrets_logger.error(
            f"Unexpected error retrieving secret {secret_name}: {type(e).__name__}"
        )
        raise


def send_cloudwatch_metrics(
    metrics: dict[str, Any], aws_region: str, execution_id: str
) -> None:
    """
    Send custom metrics to CloudWatch.

    Args:
        metrics: Dictionary containing execution metrics
        aws_region: AWS region for CloudWatch client
        execution_id: Execution ID for logging context
    """
    metrics_logger = create_execution_logger("cloudwatch_metrics", execution_id)

    try:
        metrics_logger.info("Sending metrics to CloudWatch", metrics=metrics)
        cloudwatch = boto3.client("cloudwatch", region_name=aws_region)

        # Calculate success/failure metrics
        total_items_processed = metrics["items_summarized"]
        total_errors = len(metrics["errors"])
        execution_success = total_errors == 0

        # Prepare metric data
        metric_data = [
            # Core processing metrics
            {
                "MetricName": "FeedsProcessed",
                "Value": metrics["feeds_processed"],
                "Unit": "Count",
                "Dimensions": [{"Name": "ExecutionId", "Value": execution_id}],
            },
            {
                "MetricName": "ItemsFound",
                "Value": metrics["items_found"],
                "Unit": "Count",
                "Dimensions": [{"Name": "ExecutionId", "Value": execution_id}],
            },
            {
                "MetricName": "ItemsDeduplicated",
                "Value": metrics["items_deduplicated"],
                "Unit": "Count",
                "Dimensions": [{"Name": "ExecutionId", "Value": execution_id}],
            },
            {
                "MetricName": "ItemsSummarized",
                "Value": metrics["items_summarized"],
                "Unit": "Count",
                "Dimensions": [{"Name": "ExecutionId", "Value": execution_id}],
            },
            {
                "MetricName": "MessagesSent",
                "Value": metrics["messages_sent"],
                "Unit": "Count",
                "Dimensions": [{"Name": "ExecutionId", "Value": execution_id}],
            },
            {
                "MetricName": "Errors",
                "Value": total_errors,
                "Unit": "Count",
                "Dimensions": [{"Name": "ExecutionId", "Value": execution_id}],
            },
            # Success/Failure metrics (Requirement 10.2)
            {
                "MetricName": "ExecutionSuccess",
                "Value": 1 if execution_success else 0,
                "Unit": "Count",
                "Dimensions": [
                    {
                        "Name": "Status",
                        "Value": "Success" if execution_success else "Failure",
                    }
                ],
            },
            {
                "MetricName": "ExecutionFailure",
                "Value": 0 if execution_success else 1,
                "Unit": "Count",
                "Dimensions": [
                    {
                        "Name": "Status",
                        "Value": "Success" if execution_success else "Failure",
                    }
                ],
            },
            # Processing efficiency metrics
            {
                "MetricName": "ProcessingEfficiency",
                "Value": (total_items_processed / max(metrics["items_found"], 1)) * 100,
                "Unit": "Percent",
                "Dimensions": [{"Name": "ExecutionId", "Value": execution_id}],
            },
            {
                "MetricName": "DeduplicationRate",
                "Value": (
                    metrics["items_deduplicated"] / max(metrics["items_found"], 1)
                )
                * 100,
                "Unit": "Percent",
                "Dimensions": [{"Name": "ExecutionId", "Value": execution_id}],
            },
        ]

        # Send metrics to CloudWatch in batches (CloudWatch limit is 20 metrics per call)
        batch_size = 20
        for i in range(0, len(metric_data), batch_size):
            batch = metric_data[i : i + batch_size]
            cloudwatch.put_metric_data(Namespace="RSS-Telegram-Bot", MetricData=batch)
            metrics_logger.debug(f"Sent batch of {len(batch)} metrics to CloudWatch")

        metrics_logger.info(
            "Successfully sent metrics to CloudWatch",
            metrics_sent=len(metric_data),
            namespace="RSS-Telegram-Bot",
            execution_success=execution_success,
        )

    except Exception as e:
        metrics_logger.error(f"Failed to send CloudWatch metrics: {e}", error=str(e))
        # Don't raise - metrics failure shouldn't break the main flow
