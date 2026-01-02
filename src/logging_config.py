"""Structured logging configuration for RSS Telegram Bot."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log structure
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add execution context if available
        if hasattr(record, "execution_id"):
            log_entry["execution_id"] = record.execution_id

        if hasattr(record, "component"):
            log_entry["component"] = record.component

        if hasattr(record, "feed_url"):
            log_entry["feed_url"] = record.feed_url

        if hasattr(record, "item_title"):
            log_entry["item_title"] = record.item_title

        # Add metrics if available
        if hasattr(record, "metrics"):
            log_entry["metrics"] = record.metrics

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class ExecutionLogger:
    """Logger with execution context and structured logging."""

    def __init__(self, execution_id: str, component: str = "main"):
        """Initialize execution logger.

        Args:
            execution_id: Unique identifier for this execution
            component: Component name (e.g., 'feed_processor', 'summarizer')
        """
        self.execution_id = execution_id
        self.component = component
        self.logger = logging.getLogger(f"rss_telegram_bot.{component}")
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        """Log message with execution context."""
        extra = {
            "execution_id": self.execution_id,
            "component": self.component,
            **kwargs,
        }
        self.logger.log(level, message, extra=extra)

    def info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def log_execution_start(self, **kwargs) -> None:
        """Log execution start with timestamp."""
        self.start_time = datetime.now(UTC)
        self.info(
            f"Starting {self.component} execution",
            execution_start=self.start_time.isoformat(),
            **kwargs,
        )

    def log_execution_end(self, success: bool = True, **kwargs) -> None:
        """Log execution end with timestamp and duration."""
        self.end_time = datetime.now(UTC)

        duration_seconds = None
        if self.start_time:
            duration_seconds = (self.end_time - self.start_time).total_seconds()

        self.info(
            f"Completed {self.component} execution",
            execution_end=self.end_time.isoformat(),
            execution_duration_seconds=duration_seconds,
            execution_success=success,
            **kwargs,
        )

    def log_feed_processing(self, feed_url: str, items_count: int) -> None:
        """Log feed processing with structured data."""
        self.info(
            f"Processed feed: {items_count} items found",
            feed_url=feed_url,
            items_count=items_count,
        )

    def log_item_processing(
        self, item_title: str, action: str, success: bool = True
    ) -> None:
        """Log item processing with structured data."""
        level = logging.INFO if success else logging.ERROR
        self._log_with_context(
            level,
            f"Item {action}: {item_title}",
            item_title=item_title,
            action=action,
            success=success,
        )

    def log_metrics(self, metrics: dict[str, Any]) -> None:
        """Log execution metrics."""
        self.info("Execution metrics", metrics=metrics)


def setup_structured_logging(log_level: str = "INFO") -> None:
    """Setup structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    loggers = [
        "rss_telegram_bot",
        "rss_telegram_bot.main",
        "rss_telegram_bot.feed_processor",
        "rss_telegram_bot.deduplicator",
        "rss_telegram_bot.summarizer",
        "rss_telegram_bot.telegram_publisher",
        "rss_telegram_bot.config",
    ]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.propagate = True


def create_execution_logger(
    component: str, execution_id: str | None = None
) -> ExecutionLogger:
    """Create an execution logger for a component.

    Args:
        component: Component name
        execution_id: Optional execution ID (will generate one if not provided)

    Returns:
        ExecutionLogger instance
    """
    if not execution_id:
        execution_id = f"exec_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')}"

    return ExecutionLogger(execution_id, component)
