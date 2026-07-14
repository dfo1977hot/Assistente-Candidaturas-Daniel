"""
Tests for ServiceLoader.
"""

from __future__ import annotations

from acd.core.kernel.service_loader import ServiceLoader
from acd.core.kernel.service_registry import ServiceRegistry
from acd.services.planner import PlannerService


def test_service_loader_registers_planner() -> None:
    """PlannerService is registered."""

    registry = ServiceRegistry()

    loader = ServiceLoader(registry)

    loader.load()

    service = registry.resolve(
        PlannerService,
    )

    assert isinstance(
        service,
        PlannerService,
    )