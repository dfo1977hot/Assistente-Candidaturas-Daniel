"""
Tests for Kernel CommandBus.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from acd.core.kernel.command_bus import CommandBus


@dataclass(slots=True)
class FakeCommand:
    """Fake command."""

    value: int


def test_command_bus_creation() -> None:
    """CommandBus can be instantiated."""

    bus = CommandBus()

    assert bus is not None


def test_register_handler() -> None:
    """Handlers can be registered."""

    bus = CommandBus()

    def handler(command: FakeCommand) -> int:
        return command.value

    bus.register(FakeCommand, handler)

    result = bus.dispatch(FakeCommand(10))

    assert result == 10


def test_dispatch_calls_handler() -> None:
    """Dispatch executes the registered handler."""

    bus = CommandBus()

    called = False

    def handler(command: FakeCommand) -> int:
        nonlocal called
        called = True
        return command.value * 2

    bus.register(FakeCommand, handler)

    result = bus.dispatch(FakeCommand(5))

    assert called
    assert result == 10


def test_dispatch_without_handler_raises() -> None:
    """Dispatching an unregistered command raises LookupError."""

    bus = CommandBus()

    with pytest.raises(LookupError):
        bus.dispatch(FakeCommand(1))


def test_clear_removes_handlers() -> None:
    """Clear removes every registered handler."""

    bus = CommandBus()

    def handler(command: FakeCommand) -> int:
        return command.value

    bus.register(FakeCommand, handler)

    bus.clear()

    with pytest.raises(LookupError):
        bus.dispatch(FakeCommand(1))