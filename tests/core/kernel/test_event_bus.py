"""
Tests for Kernel EventBus.
"""

from __future__ import annotations

from dataclasses import dataclass

from acd.core.kernel.event_bus import EventBus
from acd.core.kernel.events import DomainEvent, EventType


@dataclass(slots=True)
class FakeEvent(DomainEvent):
    """Fake domain event."""

    value: int = 0
    """Fake domain event."""

    value: int = 0


def test_event_bus_creation() -> None:
    """EventBus can be instantiated."""

    bus = EventBus()

    assert bus is not None


def test_subscribe_handler() -> None:
    """Handlers can be registered."""

    bus = EventBus()

    called: list[int] = []

    def handler(event: FakeEvent) -> None:
        called.append(event.value)

    bus.subscribe(FakeEvent, handler)

    bus.publish(
        FakeEvent(
            event_type=EventType.SYSTEM,
            name="fake.event",
            payload={},
            value=10,
        )
    )

    assert called == [10]


def test_publish_event_calls_handler() -> None:
    """Publishing an event calls every subscribed handler."""

    bus = EventBus()

    result: list[int] = []

    def first(event: FakeEvent) -> None:
        result.append(event.value)

    def second(event: FakeEvent) -> None:
        result.append(event.value * 2)

    bus.subscribe(FakeEvent, first)
    bus.subscribe(FakeEvent, second)

    bus.publish(
        FakeEvent(
            event_type=EventType.SYSTEM,
            name="fake.event",
            payload={},
            value=5,
        )
    )

    assert result == [5, 10]


def test_clear_removes_handlers() -> None:
    """Clear removes every registered handler."""

    bus = EventBus()

    called: list[int] = []

    def handler(event: FakeEvent) -> None:
        called.append(event.value)

    bus.subscribe(FakeEvent, handler)

    bus.clear()

    bus.publish(
        FakeEvent(
            event_type=EventType.SYSTEM,
            name="fake.event",
            payload={},
            value=1,
        )
    )

    assert called == []