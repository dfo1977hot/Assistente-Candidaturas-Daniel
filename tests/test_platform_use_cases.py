from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from acd.application.platform.platform_use_cases import (
    PlatformUseCases,
)


@pytest.fixture
def platform_use_cases(monkeypatch):
    """
    Creates PlatformUseCases with mocked services.
    """

    session = MagicMock()

    health = MagicMock()
    backup = MagicMock()
    restore = MagicMock()
    configuration = MagicMock()
    metrics = MagicMock()
    audit = MagicMock()

    logger = MagicMock()
    operation = MagicMock()
    operation.__enter__.return_value = None
    operation.__exit__.return_value = None
    logger.operation.return_value = operation

    monkeypatch.setattr(
        "acd.application.platform.platform_use_cases.HealthService",
        lambda session: health,
    )

    monkeypatch.setattr(
        "acd.application.platform.platform_use_cases.BackupService",
        lambda session, database_path=None: backup,
    )

    monkeypatch.setattr(
        "acd.application.platform.platform_use_cases.RestoreService",
        lambda session, database_path=None: restore,
    )

    monkeypatch.setattr(
        "acd.application.platform.platform_use_cases.ConfigurationService",
        lambda session: configuration,
    )

    monkeypatch.setattr(
        "acd.application.platform.platform_use_cases.MetricsService",
        lambda session: metrics,
    )

    monkeypatch.setattr(
        "acd.application.platform.platform_use_cases.AuditService",
        lambda session: audit,
    )

    monkeypatch.setattr(
        "acd.application.platform.platform_use_cases.StructuredLogger",
        lambda name: logger,
    )

    use_cases = PlatformUseCases(session)

    return (
        use_cases,
        health,
        backup,
        restore,
        configuration,
        metrics,
        audit,
        logger,
    )


def test_get_system_health(platform_use_cases):
    (
        use_cases,
        health,
        *_
    ) = platform_use_cases

    health.get_overall_health.return_value = {
        "status": "ok",
    }

    result = use_cases.get_system_health()

    assert result["status"] == "ok"

    health.get_overall_health.assert_called_once()


def test_run_specific_health_check(platform_use_cases):
    (
        use_cases,
        health,
        *_
    ) = platform_use_cases

    health.run_specific_check.return_value = {
        "healthy": True,
    }

    result = use_cases.run_health_check("database")

    assert result == {
        "check": "database",
        "result": {
            "healthy": True,
        },
    }

    health.run_specific_check.assert_called_once_with(
        "database",
    )


def test_run_specific_health_check_returns_empty(platform_use_cases):
    (
        use_cases,
        health,
        *_
    ) = platform_use_cases

    health.run_specific_check.return_value = None

    assert use_cases.run_health_check("database") == {}


def test_run_all_health_checks(platform_use_cases):
    (
        use_cases,
        health,
        *_
    ) = platform_use_cases

    health.run_all_checks.return_value = {
        "database": True,
    }

    result = use_cases.run_health_check()

    assert result == {
        "database": True,
    }

    health.run_all_checks.assert_called_once()


def test_get_health_history(platform_use_cases):
    (
        use_cases,
        health,
        *_
    ) = platform_use_cases

    history = [{"status": "ok"}]

    health.get_health_history.return_value = history

    result = use_cases.get_health_history(
        "database",
        50,
    )

    assert result == history

    health.get_health_history.assert_called_once_with(
        "database",
        50,
    )


def test_create_backup(platform_use_cases):
    (
        use_cases,
        _health,
        backup,
        _restore,
        _configuration,
        _metrics,
        audit,
        _logger,
    ) = platform_use_cases

    backup.create_manual_backup.return_value = {
        "backup_id": 10,
        "status": "completed",
    }

    result = use_cases.create_backup()

    assert result["backup_id"] == 10

    backup.create_manual_backup.assert_called_once_with(
        "./backups",
        True,
        True,
    )

    audit.log_critical_operation.assert_called_once_with(
        "CREATE_BACKUP",
        "platform",
        details={"backup_id": 10},
    )


def test_list_backups(platform_use_cases):
    (
        use_cases,
        _health,
        backup,
        *_
    ) = platform_use_cases

    backup.list_backups.return_value = [
        {"id": 1},
        {"id": 2},
    ]

    result = use_cases.list_backups("completed")

    assert len(result) == 2

    backup.list_backups.assert_called_once_with(
        "completed",
    )


def test_get_backup_info(platform_use_cases):
    (
        use_cases,
        _health,
        backup,
        *_
    ) = platform_use_cases

    backup.get_backup_info.return_value = {
        "id": 5,
    }

    result = use_cases.get_backup_info(5)

    assert result["id"] == 5

    backup.get_backup_info.assert_called_once_with(
        5,
    )


def test_restore_from_backup(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        restore,
        _configuration,
        _metrics,
        audit,
        _logger,
    ) = platform_use_cases

    restore.restore_from_backup.return_value = {
        "status": "restored",
    }

    result = use_cases.restore_from_backup(
        15,
        True,
    )

    assert result["status"] == "restored"

    restore.restore_from_backup.assert_called_once_with(
        15,
        True,
    )

    audit.log_critical_operation.assert_called_once_with(
        "RESTORE_BACKUP",
        "platform",
        details={"backup_id": 15},
    )


def test_list_restore_points(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        restore,
        *_
    ) = platform_use_cases

    restore.list_restore_points.return_value = [
        {"id": 1},
    ]

    result = use_cases.list_restore_points()

    assert result == [{"id": 1}]

    restore.list_restore_points.assert_called_once()


def test_get_config(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        configuration,
        *_
    ) = platform_use_cases

    configuration.get_config.return_value = "value"

    result = use_cases.get_config(
        "theme",
        "default",
    )

    assert result == "value"

    configuration.get_config.assert_called_once_with(
        "theme",
        "default",
    )


def test_set_config(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        configuration,
        _metrics,
        audit,
        _logger,
    ) = platform_use_cases

    configuration.set_config.return_value = {
        "success": True,
    }

    result = use_cases.set_config(
        "theme",
        "dark",
    )

    assert result["success"] is True

    configuration.set_config.assert_called_once_with(
        "theme",
        "dark",
        "string",
        "system",
    )

    audit.log_critical_operation.assert_called_once_with(
        "SET_CONFIG",
        "platform",
        details={"key": "theme"},
    )


def test_get_configuration_section(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        configuration,
        *_
    ) = platform_use_cases

    configuration.get_section.return_value = {
        "theme": "dark",
    }

    result = use_cases.get_configuration_section(
        "ui",
    )

    assert result["theme"] == "dark"

    configuration.get_section.assert_called_once_with(
        "ui",
    )


def test_export_configuration(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        configuration,
        *_
    ) = platform_use_cases

    configuration.export_config.return_value = {
        "theme": "dark",
    }

    result = use_cases.export_configuration()

    assert result["theme"] == "dark"

    configuration.export_config.assert_called_once()

def test_collect_metrics(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        _configuration,
        metrics,
        _audit,
        _logger,
    ) = platform_use_cases

    metrics.collect_system_metrics.return_value = {
        "cpu": 20,
    }

    result = use_cases.collect_metrics()

    assert result["cpu"] == 20

    metrics.collect_system_metrics.assert_called_once()


def test_get_metrics(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        _configuration,
        metrics,
        _audit,
        _logger,
    ) = platform_use_cases

    metrics.get_metrics.return_value = [
        {"cpu": 20},
    ]

    result = use_cases.get_metrics(
        "cpu",
        "system",
        12,
    )

    assert len(result) == 1

    metrics.get_metrics.assert_called_once_with(
        "cpu",
        "system",
        12,
    )


def test_get_metrics_summary(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        _configuration,
        metrics,
        _audit,
        _logger,
    ) = platform_use_cases

    metrics.get_system_summary.return_value = {
        "ok": True,
    }

    result = use_cases.get_metrics_summary()

    assert result["ok"] is True

    metrics.get_system_summary.assert_called_once()


def test_get_performance_report(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        _configuration,
        metrics,
        _audit,
        _logger,
    ) = platform_use_cases

    metrics.get_performance_report.return_value = {
        "performance": "good",
    }

    result = use_cases.get_performance_report(48)

    assert result["performance"] == "good"

    metrics.get_performance_report.assert_called_once_with(
        48,
    )


def test_get_audit_trail(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        _configuration,
        _metrics,
        audit,
        _logger,
    ) = platform_use_cases

    audit.get_audit_trail.return_value = [
        {"event": "login"},
    ]

    result = use_cases.get_audit_trail(
        "platform",
        30,
    )

    assert result[0]["event"] == "login"

    audit.get_audit_trail.assert_called_once_with(
        "platform",
        None,
        30,
    )


def test_get_user_activity(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        _configuration,
        _metrics,
        audit,
        _logger,
    ) = platform_use_cases

    audit.get_user_activity.return_value = [
        {"user": "admin"},
    ]

    result = use_cases.get_user_activity(
        "admin",
        10,
    )

    assert result[0]["user"] == "admin"

    audit.get_user_activity.assert_called_once_with(
        "admin",
        10,
    )


def test_get_failed_operations(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        _configuration,
        _metrics,
        audit,
        _logger,
    ) = platform_use_cases

    audit.get_failed_operations.return_value = [
        {"operation": "backup"},
    ]

    result = use_cases.get_failed_operations(6)

    assert result[0]["operation"] == "backup"

    audit.get_failed_operations.assert_called_once_with(
        6,
    )


def test_generate_compliance_report(platform_use_cases):
    (
        use_cases,
        _health,
        _backup,
        _restore,
        _configuration,
        _metrics,
        audit,
        _logger,
    ) = platform_use_cases

    audit.generate_compliance_report.return_value = {
        "status": "ok",
    }

    result = use_cases.generate_compliance_report(
        60,
    )

    assert result["status"] == "ok"

    audit.generate_compliance_report.assert_called_once_with(
        60,
    )


def test_get_system_overview(platform_use_cases):
    (
        use_cases,
        health,
        backup,
        _restore,
        _configuration,
        metrics,
        audit,
        _logger,
    ) = platform_use_cases

    health.get_overall_health.return_value = {
        "status": "healthy",
    }

    metrics.get_system_summary.return_value = {
        "cpu": 10,
    }

    backup.list_backups.return_value = [
        {"id": 1},
    ]

    audit.get_failed_operations.return_value = [
        {"error": "none"},
    ]

    result = use_cases.get_system_overview()

    assert result["health"]["status"] == "healthy"
    assert result["metrics"]["cpu"] == 10
    assert len(result["backups"]) == 1
    assert len(result["recent_errors"]) == 1

    health.get_overall_health.assert_called_once()
    metrics.get_system_summary.assert_called_once()
    backup.list_backups.assert_called_once()
    audit.get_failed_operations.assert_called_once_with(
        hours=24,
    )