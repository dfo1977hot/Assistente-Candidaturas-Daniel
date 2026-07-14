from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any, Protocol


class EventHandler(Protocol):
    """Protocol for event handlers."""

    def handle(self, event_type: str, data: dict[str, Any]) -> None:
        """Handle an event."""
        ...


logger = logging.getLogger(__name__)

EventCallback = Callable[[str, dict[str, Any]], None]


class EventBus:
    """Central event bus for workflow orchestration."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventCallback]] = {}

    def subscribe(self, event_type: str, handler: EventCallback) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventCallback) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event to all subscribers."""
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event_type, data)
                except Exception:
                    logger.exception("Unhandled exception while processing event %s", event_type)
