from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acd.application.platform.services.health_service import (
    HealthService,
)
from acd.domain.platform.health_report import HealthStatus


@pytest.fixture
def health_service(monkeypatch):
    """
    Creates HealthService with mocked dependencies.
    """

    session = MagicMock()

    repository = MagicMock()

    registry = MagicMock()

    logger = MagicMock()

    operation = MagicMock()
    operation.__enter__.return_value = None
    operation.__exit__.return_value = None

    logger.operation.return_value = operation

    monkeypatch.setattr(
        "acd.application.platform.services.health_service.PlatformRepository",
        lambda session: repository,
    )

    monkeypatch.setattr(
        "acd.application.platform.services.health_service.StructuredLogger",
        lambda name: logger,
    )

    monkeypatch.setattr(
        "acd.application.platform.services.health_service.get_registry",
        lambda: registry,
    )

    service = HealthService(session)

    return (
        service,
        repository,
        registry,
        logger,
    )


def create_report(
    *,
    id=1,
    check_type="database",
    status=HealthStatus.HEALTHY.value,
    message="OK",
    response_time_ms=10,
):
    return SimpleNamespace(
        id=id,
        check_type=check_type,
        status=status,
        message=message,
        response_time_ms=response_time_ms,
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
    )


def test_run_all_checks(health_service):
    service, repository, registry, logger = health_service

    registry.run_all.return_value = {
        "database": {
            "status": HealthStatus.HEALTHY.value,
            "message": "Database OK",
            "response_time_ms": 12,
        },
        "disk": {
            "status": HealthStatus.DEGRADED.value,
            "message": "Disk almost full",
            "response_time_ms": 30,
        },
    }

    result = service.run_all_checks()

    assert len(result) == 2

    assert repository.create_health_report.call_count == 2

    logger.debug.assert_called_once_with(
        "run_all_checks",
        "Starting health checks",
    )


def test_run_specific_check(health_service):
    service, repository, registry, logger = health_service

    registry.run_check.return_value = {
        "status": HealthStatus.HEALTHY.value,
        "message": "Everything OK",
        "response_time_ms": 15,
    }

    result = service.run_specific_check(
        "database",
    )

    assert result["status"] == HealthStatus.HEALTHY.value

    repository.create_health_report.assert_called_once()

    logger.debug.assert_called_once_with(
        "run_specific_check",
        "Running check: database",
    )


def test_run_specific_check_not_found(health_service):
    service, repository, registry, _ = health_service

    registry.run_check.return_value = None

    result = service.run_specific_check(
        "missing",
    )

    assert result is None

    repository.create_health_report.assert_not_called()


def test_get_overall_health(
    health_service,
):
    service, repository, registry, _ = health_service

    registry.get_overall_status.return_value = (
        HealthStatus.HEALTHY.value
    )

    registry.run_all.return_value = {
        "database": {
            "status": HealthStatus.HEALTHY.value,
        },
        "disk": {
            "status": HealthStatus.HEALTHY.value,
        },
    }

    result = service.get_overall_health()

    assert result["overall_status"] == HealthStatus.HEALTHY.value

    assert "timestamp" in result
    assert "checks" in result

    repository.get_or_create_status.assert_called_once()

    repository.update_status.assert_called_once_with(
        HealthStatus.HEALTHY.value,
    )


def test_get_overall_health_with_warning(
    health_service,
):
    service, repository, registry, _ = health_service

    registry.get_overall_status.return_value = (
        HealthStatus.DEGRADED.value
    )

    registry.run_all.return_value = {
        "database": {
            "status": HealthStatus.HEALTHY.value,
        },
        "disk": {
            "status": HealthStatus.DEGRADED.value,
        },
    }

    result = service.get_overall_health()

    assert (
        result["overall_status"]
        == HealthStatus.DEGRADED.value
    )

    repository.update_status.assert_called_once_with(
        HealthStatus.DEGRADED.value,
    )


def test_get_overall_health_unknown(
    health_service,
):
    service, repository, registry, _ = health_service

    registry.get_overall_status.return_value = (
        HealthStatus.UNKNOWN.value
    )

    registry.run_all.return_value = {}

    result = service.get_overall_health()

    assert (
        result["overall_status"]
        == HealthStatus.UNKNOWN.value
    )

    assert result["checks"] == {}

    repository.get_or_create_status.assert_called_once()

    repository.update_status.assert_called_once_with(
        HealthStatus.UNKNOWN.value,
    )


def test_get_overall_health_runs_registry_once(
    health_service,
):
    service, _, registry, _ = health_service

    registry.get_overall_status.return_value = (
        HealthStatus.HEALTHY.value
    )

    registry.run_all.return_value = {}

    service.get_overall_health()

    registry.get_overall_status.assert_called_once()

    registry.run_all.assert_called_once()


def test_get_overall_health_returns_expected_keys(
    health_service,
):
    service, _, registry, _ = health_service

    registry.get_overall_status.return_value = (
        HealthStatus.HEALTHY.value
    )

    registry.run_all.return_value = {}

    result = service.get_overall_health()

    assert {
        "overall_status",
        "timestamp",
        "checks",
    }.issubset(result.keys())


def test_get_health_history(
    health_service,
):
    service, repository, _, _ = health_service

    repository.list_health_reports.return_value = [
        create_report(
            id=1,
            check_type="database",
        ),
        create_report(
            id=2,
            check_type="disk",
            status=HealthStatus.DEGRADED.value,
        ),
    ]

    result = service.get_health_history()

    assert len(result) == 2

    assert result[0]["id"] == 1
    assert result[0]["check_type"] == "database"

    assert result[1]["status"] == HealthStatus.DEGRADED.value

    repository.list_health_reports.assert_called_once_with(
        limit=100,
        check_type=None,
    )


def test_get_health_history_filtered(
    health_service,
):
    service, repository, _, _ = health_service

    repository.list_health_reports.return_value = [
        create_report(
            check_type="database",
        ),
    ]

    result = service.get_health_history(
        check_type="database",
        limit=10,
    )

    assert len(result) == 1

    repository.list_health_reports.assert_called_once_with(
        limit=10,
        check_type="database",
    )


def test_get_health_history_empty(
    health_service,
):
    service, repository, _, _ = health_service

    repository.list_health_reports.return_value = []

    result = service.get_health_history()

    assert result == []


def test_get_health_history_without_timestamp(
    health_service,
):
    service, repository, _, _ = health_service

    report = create_report()

    report.timestamp = None

    repository.list_health_reports.return_value = [
        report,
    ]

    result = service.get_health_history()

    assert result[0]["timestamp"] is None


def test_run_all_checks_with_missing_fields(
    health_service,
):
    service, repository, registry, _ = health_service

    registry.run_all.return_value = {
        "database": {}
    }

    result = service.run_all_checks()

    assert "database" in result

    repository.create_health_report.assert_called_once_with(
        check_type="database",
        status=HealthStatus.UNKNOWN.value,
        message="",
        details=None,
        error_message=None,
        response_time_ms=0,
    )


def test_run_specific_check_with_missing_fields(
    health_service,
):
    service, repository, registry, _ = health_service

    registry.run_check.return_value = {
        "status": HealthStatus.UNKNOWN.value,
    }

    result = service.run_specific_check(
        "database",
    )

    assert result == {
        "status": HealthStatus.UNKNOWN.value,
    }

    repository.create_health_report.assert_called_once_with(
        check_type="database",
        status=HealthStatus.UNKNOWN.value,
        message="",
        details=None,
        error_message=None,
        response_time_ms=0,
    )