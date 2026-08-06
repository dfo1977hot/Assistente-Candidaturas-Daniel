from __future__ import annotations

from datetime import datetime

from acd.domain.platform.health_report import (
    HealthCheckType,
    HealthReport,
    HealthStatus,
)


def test_health_status_values():
    """HealthStatus enum must expose expected values."""

    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.DEGRADED.value == "degraded"
    assert HealthStatus.UNHEALTHY.value == "unhealthy"
    assert HealthStatus.UNKNOWN.value == "unknown"


def test_health_check_type_values():
    """HealthCheckType enum must expose expected values."""

    assert HealthCheckType.DATABASE.value == "database"
    assert HealthCheckType.FILESYSTEM.value == "filesystem"
    assert HealthCheckType.MEMORY.value == "memory"
    assert HealthCheckType.AI_SERVICE.value == "ai_service"
    assert HealthCheckType.CONNECTORS.value == "connectors"
    assert HealthCheckType.CONFIGURATION.value == "configuration"
    assert HealthCheckType.DIRECTORIES.value == "directories"
    assert HealthCheckType.PLAYWRIGHT.value == "playwright"


def create_report(status: str) -> HealthReport:
    """Create a HealthReport for tests."""

    return HealthReport(
        id=1,
        check_type=HealthCheckType.DATABASE.value,
        status=status,
        message="Database OK",
        details={"database": "online"},
        error_message=None,
        response_time_ms=12.5,
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
    )


def test_is_healthy():
    """Healthy reports must be recognized."""

    report = create_report(
        HealthStatus.HEALTHY.value,
    )

    assert report.is_healthy() is True
    assert report.is_degraded() is False
    assert report.is_unhealthy() is False


def test_is_degraded():
    """Degraded reports must be recognized."""

    report = create_report(
        HealthStatus.DEGRADED.value,
    )

    assert report.is_healthy() is False
    assert report.is_degraded() is True
    assert report.is_unhealthy() is False


def test_is_unhealthy():
    """Unhealthy reports must be recognized."""

    report = create_report(
        HealthStatus.UNHEALTHY.value,
    )

    assert report.is_healthy() is False
    assert report.is_degraded() is False
    assert report.is_unhealthy() is True


def test_unknown_status():
    """Unknown status must not be healthy."""

    report = create_report(
        HealthStatus.UNKNOWN.value,
    )

    assert report.is_healthy() is False
    assert report.is_degraded() is False
    assert report.is_unhealthy() is False


def test_to_dict():
    """Report must serialize correctly."""

    report = create_report(
        HealthStatus.HEALTHY.value,
    )

    data = report.to_dict()

    assert data["id"] == 1
    assert data["check_type"] == HealthCheckType.DATABASE.value
    assert data["status"] == HealthStatus.HEALTHY.value
    assert data["message"] == "Database OK"
    assert data["details"] == {"database": "online"}
    assert data["error_message"] is None
    assert data["response_time_ms"] == 12.5
    assert data["timestamp"] == "2026-01-01T12:00:00"


def test_to_dict_without_timestamp():
    """Serialization must support missing timestamp."""

    report = create_report(
        HealthStatus.HEALTHY.value,
    )

    report.timestamp = None

    data = report.to_dict()

    assert data["timestamp"] is None


def test_to_dict_with_error():
    """Serialization must preserve error information."""

    report = create_report(
        HealthStatus.UNHEALTHY.value,
    )

    report.error_message = "Database unavailable"

    data = report.to_dict()

    assert data["error_message"] == "Database unavailable"


def test_details_are_preserved():
    """Details dictionary must be preserved."""

    report = create_report(
        HealthStatus.HEALTHY.value,
    )

    report.details = {
        "database": "online",
        "connections": 18,
    }

    data = report.to_dict()

    assert data["details"]["database"] == "online"
    assert data["details"]["connections"] == 18