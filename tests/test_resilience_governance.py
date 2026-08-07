"""Deterministic local failure and recovery tests for Sprint J."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import threading

import pytest
from sqlalchemy import create_engine

from acd.database.create_database import create_database
from acd.infrastructure.database.sqlite_lifecycle import SQLiteDatabaseLifecycle
from acd.presentation.long_running_task_executor import LongRunningTaskExecutor, TaskState
from acd.resilience import CancellationToken, OperationCancelled, RetryPolicy, execute_with_retry


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def sleep(self, delay: float) -> None:
        self.value += delay


def test_retry_is_bounded_with_exponential_backoff_and_controlled_jitter() -> None:
    clock = FakeClock()
    attempts: list[int] = []
    delays: list[float] = []

    def operation() -> str:
        attempts.append(len(attempts) + 1)
        if len(attempts) < 3:
            raise ConnectionError("synthetic")
        return "recovered"

    value, count = execute_with_retry(
        operation,
        policy=RetryPolicy(3, 1.0, 4.0, 0.5, 10.0),
        is_retryable=lambda error: isinstance(error, ConnectionError),
        is_idempotent=True,
        clock=clock,
        sleeper=lambda delay: (delays.append(delay), clock.sleep(delay)),
        random_value=lambda: 0.5,
    )

    assert (value, count) == ("recovered", 3)
    assert delays == [1.25, 2.25]


def test_permanent_failure_is_not_retried() -> None:
    attempts = 0

    def operation() -> None:
        nonlocal attempts
        attempts += 1
        raise ValueError("permanent")

    with pytest.raises(ValueError, match="permanent"):
        execute_with_retry(
            operation,
            policy=RetryPolicy(max_attempts=3),
            is_retryable=lambda _error: False,
            is_idempotent=True,
        )
    assert attempts == 1


def test_retry_rejects_non_idempotent_operation_and_honours_deadline() -> None:
    with pytest.raises(ValueError, match="idempotent"):
        execute_with_retry(
            lambda: None,
            policy=RetryPolicy(max_attempts=2),
            is_retryable=lambda _error: True,
            is_idempotent=False,
        )

    clock = FakeClock()
    with pytest.raises(TimeoutError, match="deadline"):
        execute_with_retry(
            lambda: (_ for _ in ()).throw(ConnectionError("synthetic")),
            policy=RetryPolicy(3, 1.0, 1.0, 0.0, 0.5),
            is_retryable=lambda _error: True,
            is_idempotent=True,
            clock=clock,
            sleeper=clock.sleep,
        )


def test_cancellation_before_operation_and_between_retries() -> None:
    token = CancellationToken()
    token.request_cancellation()
    with pytest.raises(OperationCancelled):
        execute_with_retry(
            lambda: pytest.fail("operation must not start"),
            policy=RetryPolicy(),
            is_retryable=lambda _error: True,
            is_idempotent=True,
            cancellation=token,
        )

    token = CancellationToken()
    with pytest.raises(OperationCancelled):
        execute_with_retry(
            lambda: (_ for _ in ()).throw(ConnectionError("synthetic")),
            policy=RetryPolicy(max_attempts=3),
            is_retryable=lambda _error: True,
            is_idempotent=True,
            cancellation=token,
            on_retry=lambda *_args: token.request_cancellation(),
        )


def test_long_running_executor_reports_cooperative_cancellation(qtbot) -> None:
    executor = LongRunningTaskExecutor()
    started = threading.Event()
    release = threading.Event()
    cancelled: list[bool] = []
    executor.cancelled.connect(lambda: cancelled.append(True))

    def task() -> str:
        started.set()
        release.wait()
        executor.cancellation_token.raise_if_cancelled()
        return "late"

    executor.execute(task)
    qtbot.waitUntil(started.is_set)
    assert executor.cancel()
    assert executor.state is TaskState.CANCELLING
    with qtbot.waitSignal(executor.finished):
        release.set()
    assert cancelled == [True]
    assert executor.state is TaskState.CANCELLED


def test_long_running_executor_distinguishes_timeout(qtbot) -> None:
    executor = LongRunningTaskExecutor()
    release = threading.Event()
    timed_out: list[bool] = []
    executor.timed_out.connect(lambda: timed_out.append(True))

    executor.execute(lambda: release.wait() or "late", timeout_ms=10)
    qtbot.waitUntil(lambda: executor.state is TaskState.TIMED_OUT)
    with qtbot.waitSignal(executor.finished):
        release.set()
    assert timed_out == [True]
    assert executor.state is TaskState.TIMED_OUT


def _database(path: Path) -> None:
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        create_database(engine)
    finally:
        engine.dispose()


def test_backup_partial_is_removed_when_validation_fails(tmp_path, monkeypatch) -> None:
    source = tmp_path / "source.db"
    destination = tmp_path / "backup.sqlite3"
    _database(source)
    lifecycle = SQLiteDatabaseLifecycle(sleeper=lambda _delay: None)
    monkeypatch.setattr(
        lifecycle, "_validate", lambda _path: (_ for _ in ()).throw(OSError("synthetic"))
    )

    with pytest.raises(OSError, match="synthetic"):
        lifecycle.create_backup(source, destination)
    assert not destination.exists()
    assert not destination.with_suffix(".sqlite3.json").exists()


def test_restore_replace_failure_preserves_destination_and_cleans_partial(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "source.db"
    destination = tmp_path / "destination.db"
    backup = tmp_path / "backup.sqlite3"
    _database(source)
    _database(destination)
    lifecycle = SQLiteDatabaseLifecycle(sleeper=lambda _delay: None)
    lifecycle.create_backup(source, backup)
    before = destination.read_bytes()

    monkeypatch.setattr(
        "acd.infrastructure.database.sqlite_lifecycle.os.replace",
        lambda *_args: (_ for _ in ()).throw(PermissionError("synthetic")),
    )
    with pytest.raises(PermissionError, match="synthetic"):
        lifecycle.restore_backup(backup, destination)

    assert destination.read_bytes() == before
    assert not list(tmp_path.glob(".destination-restore-*"))
    with closing(sqlite3.connect(destination)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
