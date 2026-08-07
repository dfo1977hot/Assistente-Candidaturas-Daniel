"""
Tests for Kernel QueryBus.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from acd.core.kernel.query_bus import QueryBus


@dataclass(slots=True)
class FakeQuery:
    """Fake query."""

    value: int


def test_query_bus_creation() -> None:
    """QueryBus can be instantiated."""

    bus = QueryBus()

    assert bus is not None


def test_register_handler() -> None:
    """Handlers can be registered."""

    bus = QueryBus()

    def handler(query: FakeQuery) -> int:
        return query.value

    bus.register(FakeQuery, handler)

    result = bus.execute(FakeQuery(10))

    assert result == 10


def test_execute_calls_handler() -> None:
    """Execute invokes the registered handler."""

    bus = QueryBus()

    called = False

    def handler(query: FakeQuery) -> int:
        nonlocal called
        called = True
        return query.value * 2

    bus.register(FakeQuery, handler)

    result = bus.execute(FakeQuery(5))

    assert called
    assert result == 10


def test_execute_without_handler_raises() -> None:
    """Executing an unregistered query raises LookupError."""

    bus = QueryBus()

    with pytest.raises(LookupError):
        bus.execute(FakeQuery(1))


def test_clear_removes_handlers() -> None:
    """Clear removes every registered handler."""

    bus = QueryBus()

    def handler(query: FakeQuery) -> int:
        return query.value

    bus.register(FakeQuery, handler)

    bus.clear()

    with pytest.raises(LookupError):
        bus.execute(FakeQuery(1))