"""
Kernel Command Bus.

Simple synchronous CommandBus used by the ACD Kernel.
"""

from __future__ import annotations

from collections.abc import Callable

CommandHandler = Callable[[object], object]


class CommandBus:
    """Simple synchronous command bus."""

    def __init__(self) -> None:
        self._handlers: dict[type, CommandHandler] = {}

    def register(
        self,
        command_type: type,
        handler: CommandHandler,
    ) -> None:
        """Register a handler for a command."""

        self._handlers[command_type] = handler

    def dispatch(
        self,
        command: object,
    ) -> object:
        """Dispatch a command."""

        handler = self._handlers.get(type(command))

        if handler is None:
            raise LookupError(
                f"No handler registered for {type(command).__name__}"
            )

        return handler(command)

    def clear(self) -> None:
        """Remove every registered handler."""

        self._handlers.clear()