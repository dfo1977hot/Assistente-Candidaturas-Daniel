"""
Kernel Event Bus.

Simple synchronous EventBus used by the ACD Kernel.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from acd.core.kernel.events import DomainEvent

EventHandler = Callable[[DomainEvent], None]


class EventBus:
    """Simple synchronous domain event bus."""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = (
            defaultdict(list)
        )

    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type].append(handler)

    def publish(
        self,
        event: DomainEvent,
    ) -> None:
        """Publish an event."""
        for handler in self._handlers[type(event)]:
            handler(event)

    def clear(self) -> None:
        """Remove all registered handlers."""
        self._handlers.clear()