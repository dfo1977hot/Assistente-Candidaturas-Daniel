"""Dependency Injection Container."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class DependencyContainer:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._singletons: dict[type, Any] = {}
        self._factories: dict[type, Callable[[], Any]] = {}
        self._transients: dict[type, type] = {}

    # ==========================================================
    # Registration
    # ==========================================================

    def register_singleton(
        self,
        service_type: type,
        instance: Any,
    ) -> None:
        """Register singleton instance."""
        self._singletons[service_type] = instance

    def register_factory(
        self,
        service_type: type,
        factory: Callable[[], Any],
    ) -> None:
        """Register factory."""
        self._factories[service_type] = factory

    def register_transient(
        self,
        service_type: type,
        implementation: type,
    ) -> None:
        """Register transient implementation."""
        self._transients[service_type] = implementation

    # ==========================================================
    # Resolution
    # ==========================================================

    def resolve(
        self,
        service_type: type,
    ) -> Any:
        """Resolve dependency."""

        if service_type in self._singletons:
            return self._singletons[service_type]

        if service_type in self._factories:
            return self._factories[service_type]()

        if service_type in self._transients:
            implementation = self._transients[service_type]
            return implementation()

        from acd.core.kernel.exceptions import ServiceNotRegisteredError

        raise ServiceNotRegisteredError(
            f"Service '{service_type.__name__}' is not registered."
        )

    # ==========================================================
    # Utilities
    # ==========================================================

    def contains(
        self,
        service_type: type,
    ) -> bool:
        """Return True if service is registered."""

        return (
            service_type in self._singletons
            or service_type in self._factories
            or service_type in self._transients
        )

    def clear(self) -> None:
        """Remove all registrations."""

        self._singletons.clear()
        self._factories.clear()
        self._transients.clear()