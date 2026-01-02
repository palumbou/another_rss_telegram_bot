"""Unit tests for CloudWatch metrics functionality."""

from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

from src.lambda_handler import send_cloudwatch_metrics


class TestCloudWatchMetricsUnit:
    """Unit tests for CloudWatch metrics functionality."""

    def test_send_cloudwatch_metrics_success(self):
        """
        Test successful CloudWatch metrics publication.
        **Validates: Requirements 10.2**
        """
        # Test data
        metrics = {
            "feeds_processed": 3,
            "items_found": 10,
            "items_deduplicated": 2,
            "items_summarized": 8,
            "messages_sent": 8,
            "errors": [],
        }
        aws_region = "us-east-1"
        execution_id = "test-exec-123"

        with patch("boto3.client") as mock_boto_client:
            # Setup mock CloudWatch client
            mock_cloudwatch = Mock()
            mock_boto_client.return_value = mock_cloudwatch

            # Execute function
            send_cloudwatch_metrics(metrics, aws_region, execution_id)

            # Verify boto3.client was called with correct service
            mock_boto_client.assert_called_with("cloudwatch", region_name=aws_region)

            # Verify put_metric_data was called
            assert mock_cloudwatch.put_metric_data.called

            # Get the call arguments
            call_args = mock_cloudwatch.put_metric_data.call_args_list

            # Verify namespace is correct
            for call in call_args:
                args, kwargs = call
                assert kwargs["Namespace"] == "RSS-Telegram-Bot"
                assert "MetricData" in kwargs

            # Collect all metrics sent
            all_metrics = []
            for call in call_args:
                args, kwargs = call
                all_metrics.extend(kwargs["MetricData"])

            # Verify core metrics are present
            metric_names = [metric["MetricName"] for metric in all_metrics]
            expected_metrics = [
                "FeedsProcessed",
                "ItemsFound",
                "ItemsDeduplicated",
                "ItemsSummarized",
                "MessagesSent",
                "Errors",
                "ExecutionSuccess",
                "ExecutionFailure",
                "ProcessingEfficiency",
                "DeduplicationRate",
            ]

            for expected_metric in expected_metrics:
                assert (
                    expected_metric in metric_names
                ), f"Missing metric: {expected_metric}"

            # Verify specific metric values
            feeds_processed_metric = next(
                m for m in all_metrics if m["MetricName"] == "FeedsProcessed"
            )
            assert feeds_processed_metric["Value"] == 3
            assert feeds_processed_metric["Unit"] == "Count"

            items_found_metric = next(
                m for m in all_metrics if m["MetricName"] == "ItemsFound"
            )
            assert items_found_metric["Value"] == 10

            errors_metric = next(m for m in all_metrics if m["MetricName"] == "Errors")
            assert errors_metric["Value"] == 0  # len(errors) = 0

            # Verify success metrics (no errors = success)
            success_metric = next(
                m for m in all_metrics if m["MetricName"] == "ExecutionSuccess"
            )
            assert success_metric["Value"] == 1  # Success

            failure_metric = next(
                m for m in all_metrics if m["MetricName"] == "ExecutionFailure"
            )
            assert failure_metric["Value"] == 0  # No failure

            # Verify efficiency metrics
            efficiency_metric = next(
                m for m in all_metrics if m["MetricName"] == "ProcessingEfficiency"
            )
            expected_efficiency = (8 / 10) * 100  # items_summarized / items_found * 100
            assert efficiency_metric["Value"] == expected_efficiency
            assert efficiency_metric["Unit"] == "Percent"

            dedup_metric = next(
                m for m in all_metrics if m["MetricName"] == "DeduplicationRate"
            )
            expected_dedup_rate = (
                2 / 10
            ) * 100  # items_deduplicated / items_found * 100
            assert dedup_metric["Value"] == expected_dedup_rate
            assert dedup_metric["Unit"] == "Percent"

    def test_send_cloudwatch_metrics_with_errors(self):
        """
        Test CloudWatch metrics publication with errors present.
        **Validates: Requirements 10.2**
        """
        # Test data with errors
        metrics = {
            "feeds_processed": 2,
            "items_found": 5,
            "items_deduplicated": 1,
            "items_summarized": 3,
            "messages_sent": 2,
            "errors": ["Error 1", "Error 2", "Error 3"],
        }
        aws_region = "eu-west-1"
        execution_id = "test-exec-456"

        with patch("boto3.client") as mock_boto_client:
            # Setup mock CloudWatch client
            mock_cloudwatch = Mock()
            mock_boto_client.return_value = mock_cloudwatch

            # Execute function
            send_cloudwatch_metrics(metrics, aws_region, execution_id)

            # Get all metrics sent
            call_args = mock_cloudwatch.put_metric_data.call_args_list
            all_metrics = []
            for call in call_args:
                args, kwargs = call
                all_metrics.extend(kwargs["MetricData"])

            # Verify error metrics
            errors_metric = next(m for m in all_metrics if m["MetricName"] == "Errors")
            assert errors_metric["Value"] == 3  # len(errors) = 3

            # Verify failure metrics (errors present = failure)
            success_metric = next(
                m for m in all_metrics if m["MetricName"] == "ExecutionSuccess"
            )
            assert success_metric["Value"] == 0  # No success

            failure_metric = next(
                m for m in all_metrics if m["MetricName"] == "ExecutionFailure"
            )
            assert failure_metric["Value"] == 1  # Failure

            # Verify dimensions for success/failure metrics
            success_dimensions = success_metric.get("Dimensions", [])
            assert len(success_dimensions) == 1
            assert success_dimensions[0]["Name"] == "Status"
            assert success_dimensions[0]["Value"] == "Failure"

    def test_send_cloudwatch_metrics_client_error(self):
        """
        Test CloudWatch metrics publication handles client errors gracefully.
        **Validates: Requirements 10.2**
        """
        # Test data
        metrics = {
            "feeds_processed": 1,
            "items_found": 2,
            "items_deduplicated": 0,
            "items_summarized": 2,
            "messages_sent": 2,
            "errors": [],
        }
        aws_region = "us-west-2"
        execution_id = "test-exec-789"

        with patch("boto3.client") as mock_boto_client:
            # Setup mock CloudWatch client that raises an error
            mock_cloudwatch = Mock()
            mock_cloudwatch.put_metric_data.side_effect = ClientError(
                error_response={
                    "Error": {"Code": "AccessDenied", "Message": "Access denied"}
                },
                operation_name="PutMetricData",
            )
            mock_boto_client.return_value = mock_cloudwatch

            # Execute function - should not raise exception
            try:
                send_cloudwatch_metrics(metrics, aws_region, execution_id)
                # If we get here, the function handled the error gracefully
                success = True
            except Exception:
                success = False

            # Verify the function didn't raise an exception
            assert (
                success
            ), "send_cloudwatch_metrics should handle CloudWatch errors gracefully"

            # Verify put_metric_data was attempted
            assert mock_cloudwatch.put_metric_data.called

    def test_send_cloudwatch_metrics_zero_items(self):
        """
        Test CloudWatch metrics publication with zero items (edge case).
        **Validates: Requirements 10.2**
        """
        # Test data with zero items
        metrics = {
            "feeds_processed": 2,
            "items_found": 0,
            "items_deduplicated": 0,
            "items_summarized": 0,
            "messages_sent": 0,
            "errors": [],
        }
        aws_region = "ap-southeast-1"
        execution_id = "test-exec-000"

        with patch("boto3.client") as mock_boto_client:
            # Setup mock CloudWatch client
            mock_cloudwatch = Mock()
            mock_boto_client.return_value = mock_cloudwatch

            # Execute function
            send_cloudwatch_metrics(metrics, aws_region, execution_id)

            # Get all metrics sent
            call_args = mock_cloudwatch.put_metric_data.call_args_list
            all_metrics = []
            for call in call_args:
                args, kwargs = call
                all_metrics.extend(kwargs["MetricData"])

            # Verify efficiency metrics handle division by zero
            efficiency_metric = next(
                m for m in all_metrics if m["MetricName"] == "ProcessingEfficiency"
            )
            # Should be 0/1 * 100 = 0 (using max(items_found, 1) to avoid division by zero)
            assert efficiency_metric["Value"] == 0.0

            dedup_metric = next(
                m for m in all_metrics if m["MetricName"] == "DeduplicationRate"
            )
            # Should be 0/1 * 100 = 0
            assert dedup_metric["Value"] == 0.0

    def test_send_cloudwatch_metrics_dimensions(self):
        """
        Test that CloudWatch metrics include proper dimensions.
        **Validates: Requirements 10.2**
        """
        # Test data
        metrics = {
            "feeds_processed": 1,
            "items_found": 3,
            "items_deduplicated": 1,
            "items_summarized": 2,
            "messages_sent": 2,
            "errors": [],
        }
        aws_region = "eu-central-1"
        execution_id = "test-exec-dim-123"

        with patch("boto3.client") as mock_boto_client:
            # Setup mock CloudWatch client
            mock_cloudwatch = Mock()
            mock_boto_client.return_value = mock_cloudwatch

            # Execute function
            send_cloudwatch_metrics(metrics, aws_region, execution_id)

            # Get all metrics sent
            call_args = mock_cloudwatch.put_metric_data.call_args_list
            all_metrics = []
            for call in call_args:
                args, kwargs = call
                all_metrics.extend(kwargs["MetricData"])

            # Verify core metrics have ExecutionId dimension
            core_metrics = [
                "FeedsProcessed",
                "ItemsFound",
                "ItemsDeduplicated",
                "ItemsSummarized",
                "MessagesSent",
                "Errors",
            ]

            for metric_name in core_metrics:
                metric = next(m for m in all_metrics if m["MetricName"] == metric_name)
                dimensions = metric.get("Dimensions", [])
                assert len(dimensions) == 1
                assert dimensions[0]["Name"] == "ExecutionId"
                assert dimensions[0]["Value"] == execution_id

            # Verify success/failure metrics have Status dimension
            success_failure_metrics = ["ExecutionSuccess", "ExecutionFailure"]

            for metric_name in success_failure_metrics:
                metric = next(m for m in all_metrics if m["MetricName"] == metric_name)
                dimensions = metric.get("Dimensions", [])
                assert len(dimensions) == 1
                assert dimensions[0]["Name"] == "Status"
                assert dimensions[0]["Value"] in ["Success", "Failure"]
