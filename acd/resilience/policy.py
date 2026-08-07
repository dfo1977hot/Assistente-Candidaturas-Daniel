"""Bounded retry, deadline and cooperative-cancellation primitives."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
import random
import threading
import time


class FailureCategory(StrEnum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    INVALID_DATA = "invalid_data"
    STATE_CONFLICT = "state_conflict"
    INTEGRITY = "integrity"
    PERMISSION = "permission"
    CAPACITY = "capacity"
    EXTERNAL_DEPENDENCY = "external_dependency"
    FATAL = "fatal"


class OperationStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    DEGRADED = "degraded"


class OperationCancelled(RuntimeError):
    """Raised at a cooperative cancellation point."""


@dataclass(frozen=True, slots=True)
class OperationOutcome[T]:
    status: OperationStatus
    attempts: int
    duration_ms: float
    is_retryable: bool
    is_idempotent: bool
    safe_message: str
    value: object | None = None
    error_type: str | None = None
    recovery_action: str | None = None


class CancellationToken:
    """Thread-safe cooperative cancellation signal; it never kills a worker."""

    def __init__(self) -> None:
        self._requested = threading.Event()

    @property
    def is_cancellation_requested(self) -> bool:
        return self._requested.is_set()

    def request_cancellation(self) -> None:
        self._requested.set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancellation_requested:
            raise OperationCancelled("Operation was cancelled")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Retry limits for one explicitly idempotent operation."""

    max_attempts: int = 2
    base_delay_seconds: float = 0.25
    maximum_delay_seconds: float = 2.0
    jitter_seconds: float = 0.1
    deadline_seconds: float = 35.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("Retry max_attempts must be at least one")
        if (
            min(
                self.base_delay_seconds,
                self.maximum_delay_seconds,
                self.jitter_seconds,
                self.deadline_seconds,
            )
            < 0
            or self.deadline_seconds == 0
        ):
            raise ValueError("Retry timing values must be non-negative with a positive deadline")
        if self.base_delay_seconds > self.maximum_delay_seconds:
            raise ValueError("Retry base delay cannot exceed its maximum")

    def delay_for(self, failed_attempt: int, *, jitter_value: float) -> float:
        if failed_attempt < 1 or not 0.0 <= jitter_value <= 1.0:
            raise ValueError("Invalid retry delay inputs")
        exponential = min(
            self.base_delay_seconds * (2 ** (failed_attempt - 1)),
            self.maximum_delay_seconds,
        )
        return exponential + (self.jitter_seconds * jitter_value)


def execute_with_retry[T](
    operation: Callable[[], T],
    *,
    policy: RetryPolicy,
    is_retryable: Callable[[Exception], bool],
    is_idempotent: bool,
    cancellation: CancellationToken | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
    random_value: Callable[[], float] = random.random,
    on_retry: Callable[[int, float, Exception], None] | None = None,
) -> tuple[T, int]:
    """Execute an operation with bounded retries or preserve its original error."""
    if policy.max_attempts > 1 and not is_idempotent:
        raise ValueError("Retry requires an explicitly idempotent operation")
    token = cancellation or CancellationToken()
    started = clock()
    for attempt in range(1, policy.max_attempts + 1):
        token.raise_if_cancelled()
        if clock() - started >= policy.deadline_seconds:
            raise TimeoutError("Operation deadline exceeded")
        try:
            return operation(), attempt
        except OperationCancelled:
            raise
        except Exception as error:
            if attempt >= policy.max_attempts or not is_retryable(error):
                raise
            delay = policy.delay_for(attempt, jitter_value=random_value())
            remaining = policy.deadline_seconds - (clock() - started)
            if delay >= remaining:
                raise TimeoutError("Operation deadline exceeded") from error
            if on_retry is not None:
                on_retry(attempt, delay, error)
            token.raise_if_cancelled()
            sleeper(delay)
    raise RuntimeError("Retry policy exhausted without an outcome")
