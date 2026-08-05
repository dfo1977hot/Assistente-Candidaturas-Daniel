"""Qt-native execution of one long-running callable outside the UI thread."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
import logging
import time

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot

from acd.observability import log_event
from acd.resilience import CancellationToken

logger = logging.getLogger(__name__)


class TaskState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class _TaskWorker(QObject):
    """Execute one callable without accessing visual Qt objects."""

    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()

    def __init__(self, task: Callable[[], object]) -> None:
        super().__init__()
        self._task = task

    @Slot()
    def run(self) -> None:
        try:
            self.succeeded.emit(self._task())
        except Exception as error:  # pragma: no cover - exercised through signals
            self.failed.emit(error)
        finally:
            self.finished.emit()


class LongRunningTaskExecutor(QObject):
    """Run one callable in a worker thread and deliver its outcome through signals."""

    started = Signal()
    succeeded = Signal(object)
    failed = Signal(object)
    cancelled = Signal()
    timed_out = Signal()
    finished = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _TaskWorker | None = None
        self._started_at: float | None = None
        self._state = TaskState.PENDING
        self._cancellation = CancellationToken()
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._request_timeout)

    @property
    def is_running(self) -> bool:
        """Return whether this executor currently owns an active worker thread."""
        return self._thread is not None

    @property
    def queue_capacity(self) -> int:
        """The executor owns one active slot and intentionally has no backlog."""
        return 1

    @property
    def queue_depth(self) -> int:
        """Return the observable number of occupied execution slots."""
        return int(self.is_running)

    @property
    def state(self) -> TaskState:
        """Expose the explicit lifecycle state for Presentation and shutdown."""
        return self._state

    @property
    def cancellation_token(self) -> CancellationToken:
        """Token that a composed task checks between safe stages."""
        return self._cancellation

    def execute(self, task: Callable[[], object], *, timeout_ms: int | None = None) -> None:
        """Start ``task`` in a worker thread, rejecting concurrent starts."""
        if self.is_running:
            log_event(
                logger,
                logging.WARNING,
                "performance.queue.saturated",
                "Task executor capacity reached",
                status="rejected",
                queue_depth=self.queue_depth,
                queue_capacity=self.queue_capacity,
            )
            raise RuntimeError("A task is already running.")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("Task timeout must be positive")
        self._cancellation = CancellationToken()
        self._state = TaskState.PENDING
        thread = QThread(self)
        worker = _TaskWorker(task)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._handle_success)
        worker.failed.connect(self._handle_failure)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._complete)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        self._worker = worker
        self._started_at = time.perf_counter()
        worker.succeeded.connect(self._log_success)
        worker.failed.connect(self._log_failure)
        log_event(logger, logging.INFO, "task.queued", "Task queued", status="queued")
        self.started.emit()
        self._state = TaskState.RUNNING
        log_event(logger, logging.INFO, "task.started", "Task started", status="started")
        thread.start()
        if timeout_ms is not None:
            self._timeout_timer.start(timeout_ms)

    def cancel(self) -> bool:
        """Request cooperative cancellation without terminating the worker thread."""
        if not self.is_running or self._state in {TaskState.CANCELLING, TaskState.TIMED_OUT}:
            return False
        self._state = TaskState.CANCELLING
        self._cancellation.request_cancellation()
        log_event(
            logger,
            logging.INFO,
            "operation.cancel_requested",
            "Task cancellation requested",
            status="cancelling",
        )
        return True

    @Slot()
    def _request_timeout(self) -> None:
        if not self.is_running:
            return
        self._state = TaskState.TIMED_OUT
        self._cancellation.request_cancellation()
        log_event(
            logger,
            logging.WARNING,
            "operation.timed_out",
            "Task deadline expired; cooperative cancellation requested",
            status="timed_out",
            duration_ms=round(self._duration_ms(), 3),
        )

    @Slot(object)
    def _handle_success(self, result: object) -> None:
        if self._state is TaskState.TIMED_OUT:
            self.timed_out.emit()
            return
        if self._cancellation.is_cancellation_requested:
            self._state = TaskState.CANCELLED
            self.cancelled.emit()
            return
        self._state = TaskState.SUCCEEDED
        self.succeeded.emit(result)

    @Slot(object)
    def _handle_failure(self, error: object) -> None:
        if self._state is TaskState.TIMED_OUT:
            self.timed_out.emit()
            return
        if self._cancellation.is_cancellation_requested:
            self._state = TaskState.CANCELLED
            self.cancelled.emit()
            return
        self._state = TaskState.FAILED
        self.failed.emit(error)

    def _duration_ms(self) -> float:
        return 0.0 if self._started_at is None else (time.perf_counter() - self._started_at) * 1000

    @Slot(object)
    def _log_success(self, _result: object) -> None:
        if self._cancellation.is_cancellation_requested:
            return
        log_event(
            logger,
            logging.INFO,
            "task.completed",
            "Task completed",
            status="completed",
            duration_ms=round(self._duration_ms(), 3),
        )

    @Slot(object)
    def _log_failure(self, error: object) -> None:
        if self._cancellation.is_cancellation_requested:
            return
        log_event(
            logger,
            logging.ERROR,
            "task.failed",
            "Task failed",
            status="failed",
            duration_ms=round(self._duration_ms(), 3),
            error_type=type(error).__name__,
        )

    @Slot()
    def _complete(self) -> None:
        self._timeout_timer.stop()
        if self._state is TaskState.CANCELLED:
            log_event(
                logger, logging.INFO, "operation.cancelled", "Task cancelled", status="cancelled"
            )
        self._worker = None
        self._thread = None
        self._started_at = None
        self.finished.emit()
