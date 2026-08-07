from __future__ import annotations

from collections.abc import Callable


class PluginRegistry:
    """Registra plugins de conectores para permitir extensibilidade."""

    def __init__(self) -> None:
        self._plugins: dict[str, Callable[[], object]] = {}

    def register(self, name: str, factory: Callable[[], object]) -> None:
        self._plugins[name.lower().strip()] = factory

    def get(self, name: str) -> Callable[[], object] | None:
        return self._plugins.get(name.lower().strip())
