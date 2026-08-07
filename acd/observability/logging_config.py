"""The single explicit configuration point for ACD logging."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import time
from typing import Any

from acd.database.local_state import user_data_directory
from acd.observability.operation_context import (
    bind_observation_context,
    observation_context,
)
from acd.observability.sanitization import sanitize_mapping, sanitize_text
from acd.version import get_version

LOGGER_NAME = "acd"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_BACKUP_COUNT = 5
_OWNED_HANDLER = "_acd_observability_handler"


def resolve_log_directory(override: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the local log directory without creating it."""
    return (
        Path(override).expanduser().resolve()
        if override is not None
        else (user_data_directory() / "logs").resolve()
    )


class JsonLinesFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        context = observation_context()
        event = sanitize_mapping(getattr(record, "event_data", {}))
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event_name": event.pop("event_name", "technical.message"),
            "message": sanitize_text(record.getMessage()),
            "correlation_id": event.pop("correlation_id", context.correlation_id),
            "operation_id": event.pop("operation_id", context.operation_id),
            "component": event.pop("component", record.name),
            "status": event.pop("status", "unknown"),
            "app_version": get_version(),
            "process_id": record.process,
            "thread_name": record.threadName,
            **event,
        }
        if record.exc_info:
            payload["error_type"] = record.exc_info[0].__name__
            payload["exception"] = sanitize_text(record.exc_info[1])
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=sanitize_text)


def configure_logging(
    *,
    log_directory: str | os.PathLike[str] | None = None,
    level: int | str = logging.INFO,
    console: bool = True,
    file: bool = True,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> Path | None:
    """Configure owned handlers once and return the file path, if enabled."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False
    if any(getattr(handler, _OWNED_HANDLER, False) for handler in logger.handlers):
        for handler in logger.handlers:
            if getattr(handler, _OWNED_HANDLER, False) and isinstance(handler, RotatingFileHandler):
                return Path(handler.baseFilename)
        return None
    formatter = JsonLinesFormatter()
    log_path: Path | None = None
    if console:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        setattr(handler, _OWNED_HANDLER, True)
        logger.addHandler(handler)
    if file:
        directory = resolve_log_directory(log_directory)
        try:
            directory.mkdir(parents=True, exist_ok=True)
            log_path = directory / "acd.jsonl"
            handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            handler.setFormatter(formatter)
            setattr(handler, _OWNED_HANDLER, True)
            logger.addHandler(handler)
        except OSError:
            if not console:
                raise
            log_path = None
            log_event(
                logger,
                logging.WARNING,
                "logging.file.unavailable",
                "File logging unavailable; console logging remains active",
                status="degraded",
            )
    return log_path


def close_logging() -> None:
    """Close and remove only handlers owned by ACD observability."""
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        if getattr(handler, _OWNED_HANDLER, False):
            logger.removeHandler(handler)
            handler.flush()
            handler.close()


def log_event(
    logger: logging.Logger,
    level: int,
    event_name: str,
    message: str,
    *,
    status: str,
    component: str | None = None,
    **fields: Any,
) -> None:
    context = observation_context()
    event_data = sanitize_mapping(fields)
    event_data.update(
        {
            "event_name": event_name,
            "status": status,
            "component": component or logger.name,
            "correlation_id": context.correlation_id,
            "operation_id": context.operation_id,
        }
    )
    logger.log(level, sanitize_text(message), extra={"event_data": event_data})


@contextmanager
def observed_operation(
    logger: logging.Logger,
    event_prefix: str,
    *,
    component: str | None = None,
    **fields: Any,
) -> Iterator[None]:
    """Emit correlated start/completion/failure events with monotonic duration."""
    with bind_observation_context() as context:
        start = time.perf_counter()
        log_event(
            logger,
            logging.INFO,
            f"{event_prefix}.started",
            "Operation started",
            status="started",
            component=component,
            **fields,
        )
        try:
            yield
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            log_event(
                logger,
                logging.ERROR,
                f"{event_prefix}.failed",
                "Operation failed",
                status="failed",
                component=component,
                duration_ms=round(duration, 3),
                error_type=type(exc).__name__,
                correlation_id=context.correlation_id,
            )
            raise
        else:
            duration = (time.perf_counter() - start) * 1000
            log_event(
                logger,
                logging.INFO,
                f"{event_prefix}.completed",
                "Operation completed",
                status="completed",
                component=component,
                duration_ms=round(duration, 3),
                **fields,
            )
