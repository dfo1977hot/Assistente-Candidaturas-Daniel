"""
Application Service Loader.
"""

from __future__ import annotations

from collections.abc import Callable

from acd.core.kernel.service_registry import ServiceRegistry
from acd.services.planner import PlannerService

Factory = Callable[[], object]


class ServiceLoader:
    """Registers application services."""

    def __init__(
        self,
        registry: ServiceRegistry,
    ) -> None:
        self._registry = registry

    def load(self) -> None:
        """Load every application service."""

        services: dict[type, Factory] = {
            PlannerService: PlannerService,
        }

        for service_type, factory in services.items():
            self._registry.register(
                service_type,
                factory(),
            )