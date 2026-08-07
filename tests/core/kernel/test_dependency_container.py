"""Tests for DependencyContainer."""

from __future__ import annotations

import pytest

from acd.core.kernel.dependency_container import DependencyContainer
from acd.core.kernel.exceptions import ServiceNotRegisteredError


class ServiceA:
    """Fake service."""


class ServiceB:
    """Fake service."""


class ServiceC:
    """Fake service."""


class ServiceD:
    """Fake service."""


def test_register_singleton() -> None:
    """Should register singleton."""

    container = DependencyContainer()

    service = ServiceA()

    container.register_singleton(
        ServiceA,
        service,
    )

    assert container.contains(ServiceA)


def test_resolve_singleton() -> None:
    """Should always return same singleton."""

    container = DependencyContainer()

    service = ServiceA()

    container.register_singleton(
        ServiceA,
        service,
    )

    first = container.resolve(ServiceA)
    second = container.resolve(ServiceA)

    assert first is second


def test_register_factory() -> None:
    """Should register factory."""

    container = DependencyContainer()

    container.register_factory(
        ServiceB,
        lambda: ServiceB(),
    )

    assert container.contains(ServiceB)


def test_resolve_factory() -> None:
    """Factory should create new instance."""

    container = DependencyContainer()

    container.register_factory(
        ServiceB,
        lambda: ServiceB(),
    )

    first = container.resolve(ServiceB)
    second = container.resolve(ServiceB)

    assert isinstance(first, ServiceB)
    assert isinstance(second, ServiceB)
    assert first is not second


def test_register_transient() -> None:
    """Should register transient."""

    container = DependencyContainer()

    container.register_transient(
        ServiceC,
        ServiceC,
    )

    assert container.contains(ServiceC)


def test_resolve_transient() -> None:
    """Transient should create new instance."""

    container = DependencyContainer()

    container.register_transient(
        ServiceC,
        ServiceC,
    )

    first = container.resolve(ServiceC)
    second = container.resolve(ServiceC)

    assert isinstance(first, ServiceC)
    assert isinstance(second, ServiceC)
    assert first is not second


def test_contains_returns_false() -> None:
    """Should return False when service is absent."""

    container = DependencyContainer()

    assert not container.contains(ServiceD)


def test_clear() -> None:
    """Should remove every registration."""

    container = DependencyContainer()

    container.register_singleton(
        ServiceA,
        ServiceA(),
    )

    container.register_factory(
        ServiceB,
        lambda: ServiceB(),
    )

    container.register_transient(
        ServiceC,
        ServiceC,
    )

    container.clear()

    assert not container.contains(ServiceA)
    assert not container.contains(ServiceB)
    assert not container.contains(ServiceC)


def test_service_not_registered() -> None:
    """Should raise ServiceNotRegisteredError."""

    container = DependencyContainer()

    with pytest.raises(ServiceNotRegisteredError):
        container.resolve(ServiceA)