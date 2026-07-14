"""
Kernel Service Registry.

Stores singleton services registered by type.
"""

from __future__ import annotations


class ServiceRegistry:
    """Registry of application services."""

    def __init__(self) -> None:
        self._services: dict[type, object] = {}

    def register(
        self,
        service_type: type,
        instance: object,
    ) -> None:
        """Register a service instance."""

        self._services[service_type] = instance

    def resolve(
        self,
        service_type: type,
    ) -> object:
        """Resolve a registered service."""

        try:
            return self._services[service_type]
        except KeyError as exc:
            raise LookupError(
                f"Service not registered: {service_type.__name__}"
            ) from exc

    def contains(
        self,
        service_type: type,
    ) -> bool:
        """Return True if a service is registered."""

        return service_type in self._services

    def clear(self) -> None:
        """Remove every registered service."""

        self._services.clear()