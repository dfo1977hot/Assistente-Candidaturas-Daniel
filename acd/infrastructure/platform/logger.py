"""Structured logging framework for the platform."""

import logging
import uuid
from typing import Any
from datetime import datetime
from contextlib import contextmanager
import time

from acd.domain.platform.system_log import SystemLog, LogLevel


class StructuredLogger:
    """Structured logging with correlation tracking."""

    def __init__(self, name: str) -> None:
        """Initialize logger.

        Args:
            name: Logger name (module)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.correlation_id: str | None = None
        self.request_id: str | None = None

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for request tracking.

        Args:
            correlation_id: Correlation ID
        """
        self.correlation_id = correlation_id

    def set_request_id(self, request_id: str) -> None:
        """Set request ID.

        Args:
            request_id: Request ID
        """
        self.request_id = request_id

    def get_context(self) -> dict[str, Any]:
        """Get logging context.

        Returns:
            Context dictionary
        """
        return {
            "correlation_id": self.correlation_id or str(uuid.uuid4()),
            "request_id": self.request_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _log(
        self,
        level: str,
        operation: str,
        message: str,
        duration_ms: float = 0.0,
        result: str = "success",
        error_type: str | None = None,
        status_code: int | None = None,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SystemLog:
        """Internal log method.

        Args:
            level: Log level
            operation: Operation name
            message: Log message
            duration_ms: Operation duration
            result: Operation result
            error_type: Error type if failed
            status_code: Status code
            context: Additional context
            metadata: Additional metadata

        Returns:
            SystemLog entity
        """
        log_context = self.get_context()
        log_context.update(context or {})

        log_data = {
            "level": level,
            "module": self.name,
            "operation": operation,
            "message": message,
            "duration_ms": duration_ms,
            "result": result,
            "error_type": error_type,
            "status_code": status_code,
            "correlation_id": log_context.get("correlation_id"),
            "request_id": log_context.get("request_id"),
            "context": log_context,
            "metadata": metadata or {},
        }

        # Also log to Python logger
        log_level = getattr(logging, level, logging.INFO)
        self.logger.log(log_level, f"{operation}: {message}")

        return log_data

    def debug(
        self,
        operation: str,
        message: str,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log debug message.

        Args:
            operation: Operation name
            message: Log message
            context: Additional context
            metadata: Additional metadata

        Returns:
            Log data
        """
        return self._log(
            LogLevel.DEBUG.value,
            operation,
            message,
            context=context,
            metadata=metadata,
        )

    def info(
        self,
        operation: str,
        message: str,
        duration_ms: float = 0.0,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log info message.

        Args:
            operation: Operation name
            message: Log message
            duration_ms: Operation duration
            context: Additional context
            metadata: Additional metadata

        Returns:
            Log data
        """
        return self._log(
            LogLevel.INFO.value,
            operation,
            message,
            duration_ms=duration_ms,
            result="success",
            context=context,
            metadata=metadata,
        )

    def warning(
        self,
        operation: str,
        message: str,
        duration_ms: float = 0.0,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log warning message.

        Args:
            operation: Operation name
            message: Log message
            duration_ms: Operation duration
            context: Additional context
            metadata: Additional metadata

        Returns:
            Log data
        """
        return self._log(
            LogLevel.WARNING.value,
            operation,
            message,
            duration_ms=duration_ms,
            result="partial",
            context=context,
            metadata=metadata,
        )

    def error(
        self,
        operation: str,
        message: str,
        error_type: str | None = None,
        duration_ms: float = 0.0,
        status_code: int | None = None,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log error message.

        Args:
            operation: Operation name
            message: Log message
            error_type: Error type
            duration_ms: Operation duration
            status_code: Status code
            context: Additional context
            metadata: Additional metadata

        Returns:
            Log data
        """
        return self._log(
            LogLevel.ERROR.value,
            operation,
            message,
            duration_ms=duration_ms,
            result="failure",
            error_type=error_type,
            status_code=status_code,
            context=context,
            metadata=metadata,
        )

    def critical(
        self,
        operation: str,
        message: str,
        error_type: str | None = None,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log critical message.

        Args:
            operation: Operation name
            message: Log message
            error_type: Error type
            context: Additional context
            metadata: Additional metadata

        Returns:
            Log data
        """
        return self._log(
            LogLevel.CRITICAL.value,
            operation,
            message,
            result="failure",
            error_type=error_type,
            context=context,
            metadata=metadata,
        )

    @contextmanager
    def operation(
        self,
        operation_name: str,
        level: str = LogLevel.INFO.value,
    ):
        """Context manager for operation timing.

        Args:
            operation_name: Name of operation
            level: Log level

        Yields:
            None
        """
        start_time = time.time()
        try:
            yield
            duration_ms = (time.time() - start_time) * 1000
            if level == LogLevel.DEBUG.value:
                self.debug(operation_name, f"Completed in {duration_ms:.2f}ms")
            else:
                self.info(operation_name, f"Completed in {duration_ms:.2f}ms", duration_ms=duration_ms)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.error(
                operation_name,
                f"Failed: {str(e)}",
                error_type=type(e).__name__,
                duration_ms=duration_ms,
            )
            raise
