"""Tests for application bootstrap."""

from __future__ import annotations

from acd.core.kernel.application_context import ApplicationContext
from acd.core.kernel.bootstrap import Bootstrap
from acd.core.kernel.dependency_container import DependencyContainer
from acd.core.kernel.kernel import Kernel
from acd.core.kernel.lifecycle import LifecycleState
from acd.services.planner import PlannerService


def test_bootstrap_creation() -> None:
    """Bootstrap is created correctly."""

    bootstrap = Bootstrap()

    assert bootstrap.kernel is not None
    assert bootstrap.context is not None
    assert bootstrap.container is not None


def test_bootstrap_initialization() -> None:
    """Bootstrap initializes correctly."""

    bootstrap = Bootstrap()

    bootstrap.initialize()

    assert bootstrap.state == LifecycleState.READY


def test_bootstrap_registers_kernel() -> None:
    """Kernel is automatically registered."""

    bootstrap = Bootstrap()

    kernel = bootstrap.resolve_service(Kernel)

    assert kernel is bootstrap.kernel


def test_bootstrap_registers_context() -> None:
    """ApplicationContext is automatically registered."""

    bootstrap = Bootstrap()

    context = bootstrap.resolve_service(
        ApplicationContext
    )

    assert context is bootstrap.context


def test_bootstrap_registers_container() -> None:
    """DependencyContainer is automatically registered."""

    bootstrap = Bootstrap()

    container = bootstrap.resolve_service(
        DependencyContainer
    )

    assert container is bootstrap.container


def test_bootstrap_registers_planner_service() -> None:
    """PlannerService is automatically registered."""

    bootstrap = Bootstrap()

    planner = bootstrap.resolve_service(
        PlannerService
    )

    assert isinstance(
        planner,
        PlannerService,
    )