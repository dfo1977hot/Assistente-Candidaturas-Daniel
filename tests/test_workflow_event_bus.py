from __future__ import annotations

import logging

from acd.infrastructure.workflow.workflow_event_bus import EventBus


def test_subscribe_registers_handler():
    """Subscribe must register a handler."""

    bus = EventBus()

    received: list[tuple[str, dict]] = []

    def handler(event_type: str, data: dict) -> None:
        received.append((event_type, data))

    bus.subscribe(
        "workflow_started",
        handler,
    )

    bus.publish(
        "workflow_started",
        {"id": 1},
    )

    assert len(received) == 1
    assert received[0][0] == "workflow_started"
    assert received[0][1]["id"] == 1


def test_unsubscribe_removes_handler():
    """Unsubscribe must remove a handler."""

    bus = EventBus()

    received: list[tuple[str, dict]] = []

    def handler(event_type: str, data: dict) -> None:
        received.append((event_type, data))

    bus.subscribe(
        "workflow_started",
        handler,
    )

    bus.unsubscribe(
        "workflow_started",
        handler,
    )

    bus.publish(
        "workflow_started",
        {"id": 1},
    )

    assert received == []


def test_publish_without_subscribers():
    """Publishing without subscribers must not fail."""

    bus = EventBus()

    bus.publish(
        "unknown_event",
        {"value": 123},
    )


def test_multiple_handlers_receive_same_event():
    """All registered handlers must receive the event."""

    bus = EventBus()

    first: list[str] = []
    second: list[str] = []

    def handler_one(event_type: str, data: dict) -> None:
        first.append(event_type)

    def handler_two(event_type: str, data: dict) -> None:
        second.append(event_type)

    bus.subscribe(
        "workflow_completed",
        handler_one,
    )

    bus.subscribe(
        "workflow_completed",
        handler_two,
    )

    bus.publish(
        "workflow_completed",
        {},
    )

    assert first == ["workflow_completed"]
    assert second == ["workflow_completed"]


def test_handler_exception_is_logged(caplog):
    """Exceptions raised by handlers must be logged."""

    bus = EventBus()

    def failing_handler(event_type: str, data: dict) -> None:
        raise RuntimeError("boom")

    bus.subscribe(
        "workflow_started",
        failing_handler,
    )

    with caplog.at_level(logging.ERROR):
        bus.publish(
            "workflow_started",
            {},
        )

    assert "Unhandled exception while processing event" in caplog.text


def test_publish_calls_handlers_in_registration_order():
    """Handlers must execute in registration order."""

    bus = EventBus()

    order: list[int] = []

    def first(event_type: str, data: dict) -> None:
        order.append(1)

    def second(event_type: str, data: dict) -> None:
        order.append(2)

    bus.subscribe(
        "event",
        first,
    )

    bus.subscribe(
        "event",
        second,
    )

    bus.publish(
        "event",
        {},
    )

    assert order == [1, 2]


def test_subscribe_allows_duplicate_handlers():
    """The same handler may be registered more than once."""

    bus = EventBus()

    calls = 0

    def handler(event_type: str, data: dict) -> None:
        nonlocal calls
        calls += 1

    bus.subscribe(
        "event",
        handler,
    )

    bus.subscribe(
        "event",
        handler,
    )

    bus.publish(
        "event",
        {},
    )

    assert calls == 2