"""
Kernel integration tests.
"""

from __future__ import annotations

from dataclasses import dataclass

from acd.core.kernel.kernel import Kernel


@dataclass(slots=True)
class FakeService:
    """Fake service."""


@dataclass(slots=True)
class FakeCommand:
    """Fake command."""

    value: int


@dataclass(slots=True)
class FakeQuery:
    """Fake query."""

    value: int


def test_kernel_registers_service() -> None:
    """Kernel resolves registered services."""

    kernel = Kernel()

    service = FakeService()

    kernel.services.register(FakeService, service)

    resolved = kernel.services.resolve(FakeService)

    assert resolved is service


def test_kernel_dispatches_command() -> None:
    """Kernel dispatches commands."""

    kernel = Kernel()

    kernel.commands.register(
        FakeCommand,
        lambda command: command.value * 2,
    )

    result = kernel.commands.dispatch(
        FakeCommand(5)
    )

    assert result == 10


def test_kernel_executes_query() -> None:
    """Kernel executes queries."""

    kernel = Kernel()

    kernel.queries.register(
        FakeQuery,
        lambda query: query.value + 10,
    )

    result = kernel.queries.execute(
        FakeQuery(5)
    )

    assert result == 15

def test_kernel_registers_core_services() -> None:
    """Kernel automatically registers its core services."""

    from acd.core.kernel.command_bus import CommandBus
    from acd.core.kernel.dependency_container import (
        DependencyContainer,
    )
    from acd.core.kernel.event_bus import EventBus
    from acd.core.kernel.query_bus import QueryBus

    kernel = Kernel()

    assert kernel.services.resolve(EventBus) is kernel.events
    assert kernel.services.resolve(CommandBus) is kernel.commands
    assert kernel.services.resolve(QueryBus) is kernel.queries
    assert (
        kernel.services.resolve(DependencyContainer)
        is kernel.container
    )

def test_kernel_publishes_event() -> None:
    """Kernel publishes events."""

    from acd.core.kernel.events import (
        DomainEvent,
        EventType,
    )

    received = []

    kernel = Kernel()

    kernel.events.subscribe(
        DomainEvent,
        lambda event: received.append(event.name),
    )

    kernel.events.publish(
        DomainEvent(
            event_type=EventType.SYSTEM,
            name="kernel.started",
            payload={},
        )
    )

    assert received == [
        "kernel.started"
    ]