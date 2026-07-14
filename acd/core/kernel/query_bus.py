"""
Kernel Query Bus.

Simple synchronous QueryBus used by the ACD Kernel.
"""

from __future__ import annotations

from collections.abc import Callable

QueryHandler = Callable[[object], object]


class QueryBus:
    """Simple synchronous query bus."""

    def __init__(self) -> None:
        self._handlers: dict[type, QueryHandler] = {}

    def register(
        self,
        query_type: type,
        handler: QueryHandler,
    ) -> None:
        """Register a handler for a query."""

        self._handlers[query_type] = handler

    def execute(
        self,
        query: object,
    ) -> object:
        """Execute a query."""

        handler = self._handlers.get(type(query))

        if handler is None:
            raise LookupError(
                f"No handler registered for {type(query).__name__}"
            )

        return handler(query)

    def clear(self) -> None:
        """Remove all registered handlers."""

        self._handlers.clear()