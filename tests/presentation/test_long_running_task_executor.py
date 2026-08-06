"""Qt tests for the reusable Presentation task executor."""

from __future__ import annotations

import inspect
import threading

from acd.presentation.long_running_task_executor import LongRunningTaskExecutor


def test_executor_delivers_success_from_a_worker_thread(qtbot) -> None:
    executor = LongRunningTaskExecutor()
    executed_on: list[int] = []
    results: list[object] = []
    executor.succeeded.connect(results.append)

    with qtbot.waitSignal(executor.finished):
        executor.execute(lambda: executed_on.append(threading.get_ident()) or {"ok": True})

    assert executed_on != [threading.get_ident()]
    assert results == [{"ok": True}]
    assert not executor.is_running


def test_executor_reports_failure_and_allows_a_later_task(qtbot) -> None:
    executor = LongRunningTaskExecutor()
    errors: list[Exception] = []
    executor.failed.connect(errors.append)

    def fail() -> None:
        raise ValueError("expected")

    with qtbot.waitSignal(executor.finished):
        executor.execute(fail)
    assert isinstance(errors[0], ValueError)

    results: list[object] = []
    executor.succeeded.connect(results.append)
    with qtbot.waitSignal(executor.finished):
        executor.execute(lambda: None)
    assert results == [None]


def test_executor_keeps_the_ui_event_loop_responsive(qtbot) -> None:
    executor = LongRunningTaskExecutor()
    release = threading.Event()
    started = threading.Event()
    processed = []

    def task() -> str:
        started.set()
        release.wait()
        return "done"

    executor.execute(task)
    qtbot.waitUntil(started.is_set)
    qtbot.waitUntil(lambda: executor.is_running)
    processed.append(True)
    with qtbot.waitSignal(executor.finished):
        release.set()
    assert processed == [True]


def test_executor_does_not_depend_on_business_or_widget_modules() -> None:
    source = inspect.getsource(LongRunningTaskExecutor)
    for forbidden in ("acd.application", "acd.infrastructure", "QWidget", "UseCase"):
        assert forbidden not in source


def test_executor_can_be_discarded_after_its_thread_finishes(qtbot) -> None:
    executor = LongRunningTaskExecutor()
    thread = None

    with qtbot.waitSignal(executor.finished):
        executor.execute(lambda: "complete")
        thread = executor._thread

    assert thread is not None
    assert not thread.isRunning()
    executor.deleteLater()
