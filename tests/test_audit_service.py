from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acd.application.platform.services.audit_service import AuditService
from acd.domain.platform.system_log import LogLevel


@pytest.fixture
def audit_service(monkeypatch):
    """
    Creates AuditService with mocked dependencies.
    """

    session = MagicMock()

    repository = MagicMock()

    logger = MagicMock()

    operation = MagicMock()
    operation.__enter__.return_value = None
    operation.__exit__.return_value = None

    logger.operation.return_value = operation

    monkeypatch.setattr(
        "acd.application.platform.services.audit_service.PlatformRepository",
        lambda session: repository,
    )

    monkeypatch.setattr(
        "acd.application.platform.services.audit_service.StructuredLogger",
        lambda name: logger,
    )

    service = AuditService(session)

    return (
        service,
        repository,
        logger,
    )


def create_log(
    *,
    id=1,
    level="warning",
    module="platform",
    operation="backup",
    message="message",
    result="success",
    user_id="admin",
    error_type=None,
    metadata=None,
):
    return SimpleNamespace(
        id=id,
        level=level,
        module=module,
        operation=operation,
        message=message,
        result=result,
        user_id=user_id,
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
        metadata=metadata or {},
        error_type=error_type,
        correlation_id="corr-id",
    )


def test_log_critical_operation(audit_service):
    service, repository, _ = audit_service

    repository.create_log.return_value = create_log(id=99)

    result = service.log_critical_operation(
        "CREATE_BACKUP",
        "platform",
        user_id="admin",
        details={"backup": 1},
    )

    assert result["id"] == 99
    assert result["operation"] == "CREATE_BACKUP"

    repository.create_log.assert_called_once_with(
        LogLevel.WARNING.value,
        "platform",
        "CREATE_BACKUP",
        "Critical operation: CREATE_BACKUP",
        user_id="admin",
        result="success",
        metadata={"backup": 1},
    )


def test_get_audit_trail(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(
            id=1,
            operation="backup",
        ),
        create_log(
            id=2,
            operation="restore",
        ),
    ]

    result = service.get_audit_trail()

    assert len(result) == 2

    repository.list_logs.assert_called_once_with(
        level=LogLevel.WARNING.value,
        module=None,
        hours_back=168,
    )


def test_get_audit_trail_filters_operation(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(operation="backup"),
        create_log(operation="restore"),
    ]

    result = service.get_audit_trail(
        operation="backup",
    )

    assert len(result) == 1
    assert result[0]["operation"] == "backup"


def test_get_user_activity(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(user_id="alice"),
        create_log(user_id="bob"),
    ]

    result = service.get_user_activity(
        "alice",
    )

    assert len(result) == 1
    assert result[0]["user_id"] == "alice"

    repository.list_logs.assert_called_once_with(
        hours_back=168,
    )


def test_get_failed_operations(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(
            id=1,
            level=LogLevel.ERROR.value,
            error_type="RuntimeError",
        ),
        create_log(
            id=2,
            level=LogLevel.ERROR.value,
            error_type="ValueError",
        ),
    ]

    result = service.get_failed_operations(48)

    assert len(result) == 2
    assert result[0]["error_type"] == "RuntimeError"
    assert result[1]["error_type"] == "ValueError"

    repository.list_logs.assert_called_once_with(
        level=LogLevel.ERROR.value,
        hours_back=48,
    )


def test_generate_compliance_report(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(
            module="platform",
            level=LogLevel.WARNING.value,
        ),
        create_log(
            module="platform",
            level=LogLevel.ERROR.value,
        ),
        create_log(
            module="workflow",
            level=LogLevel.WARNING.value,
        ),
    ]

    report = service.generate_compliance_report(30)

    assert report["period_days"] == 30
    assert report["total_operations"] == 3
    assert report["total_errors"] == 1
    assert report["total_warnings"] == 2

    assert report["modules"]["platform"]["total"] == 2
    assert report["modules"]["platform"]["errors"] == 1
    assert report["modules"]["platform"]["warnings"] == 1

    assert report["modules"]["workflow"]["total"] == 1
    assert report["modules"]["workflow"]["warnings"] == 1

    assert abs(report["error_rate"] - (100 / 3)) < 0.001


def test_generate_compliance_report_without_logs(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = []

    report = service.generate_compliance_report()

    assert report["total_operations"] == 0
    assert report["total_errors"] == 0
    assert report["total_warnings"] == 0
    assert report["error_rate"] == 0
    assert report["modules"] == {}


def test_generate_compliance_report_only_errors(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(
            level=LogLevel.ERROR.value,
        ),
        create_log(
            level=LogLevel.ERROR.value,
        ),
    ]

    report = service.generate_compliance_report()

    assert report["total_operations"] == 2
    assert report["total_errors"] == 2
    assert report["total_warnings"] == 0
    assert report["error_rate"] == 100


def test_generate_compliance_report_only_warnings(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(
            level=LogLevel.WARNING.value,
        ),
        create_log(
            level=LogLevel.WARNING.value,
        ),
        create_log(
            level=LogLevel.WARNING.value,
        ),
    ]

    report = service.generate_compliance_report()

    assert report["total_errors"] == 0
    assert report["total_warnings"] == 3
    assert report["error_rate"] == 0


def test_generate_compliance_report_multiple_modules(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(
            module="platform",
            level=LogLevel.ERROR.value,
        ),
        create_log(
            module="platform",
            level=LogLevel.WARNING.value,
        ),
        create_log(
            module="workflow",
            level=LogLevel.WARNING.value,
        ),
        create_log(
            module="workflow",
            level=LogLevel.WARNING.value,
        ),
    ]

    report = service.generate_compliance_report()

    assert report["modules"]["platform"]["total"] == 2
    assert report["modules"]["platform"]["errors"] == 1
    assert report["modules"]["platform"]["warnings"] == 1

    assert report["modules"]["workflow"]["total"] == 2
    assert report["modules"]["workflow"]["errors"] == 0
    assert report["modules"]["workflow"]["warnings"] == 2


def test_export_audit_log_default_period(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(
            id=1,
            level=LogLevel.WARNING.value,
        ),
        create_log(
            id=2,
            level=LogLevel.ERROR.value,
        ),
    ]

    result = service.export_audit_log()

    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2

    repository.list_logs.assert_called_once()

    hours_back = repository.list_logs.call_args.kwargs["hours_back"]

    # Aproximadamente 30 dias
    assert 719 <= hours_back <= 721


def test_export_audit_log_custom_period(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(id=10),
    ]

    start = datetime(2026, 1, 1, 0, 0, 0)
    end = datetime(2026, 1, 3, 0, 0, 0)

    result = service.export_audit_log(
        start_date=start,
        end_date=end,
    )

    assert len(result) == 1

    repository.list_logs.assert_called_once_with(
        hours_back=48,
    )


def test_export_audit_log_without_start_date(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = []

    end = datetime(2026, 2, 1)

    result = service.export_audit_log(
        end_date=end,
    )

    assert result == []

    repository.list_logs.assert_called_once()

    hours_back = repository.list_logs.call_args.kwargs["hours_back"]

    assert 719 <= hours_back <= 721


def test_export_audit_log_without_end_date(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = []

    start = datetime.now() - timedelta(days=10)

    result = service.export_audit_log(
        start_date=start,
    )

    assert result == []

    repository.list_logs.assert_called_once()

    hours_back = repository.list_logs.call_args.kwargs["hours_back"]

    assert 239 <= hours_back <= 241


def test_export_audit_log_contains_expected_fields(audit_service):
    service, repository, _ = audit_service

    repository.list_logs.return_value = [
        create_log(
            id=123,
            level=LogLevel.ERROR.value,
            module="platform",
            operation="backup",
            message="failure",
            user_id="admin",
            result="failed",
            error_type="RuntimeError",
        ),
    ]

    result = service.export_audit_log()

    exported = result[0]

    assert exported["id"] == 123
    assert exported["level"] == LogLevel.ERROR.value
    assert exported["module"] == "platform"
    assert exported["operation"] == "backup"
    assert exported["message"] == "failure"
    assert exported["user_id"] == "admin"
    assert exported["result"] == "failed"
    assert exported["error_type"] == "RuntimeError"
    assert exported["correlation_id"] == "corr-id"
    assert exported["timestamp"] is not None


def test_log_critical_operation_without_timestamp(audit_service):
    service, repository, _ = audit_service

    log = create_log(id=77)
    log.timestamp = None

    repository.create_log.return_value = log

    result = service.log_critical_operation(
        "RESTORE",
        "platform",
    )

    assert result["id"] == 77
    assert result["timestamp"] is None


def test_get_audit_trail_without_timestamp(audit_service):
    service, repository, _ = audit_service

    log = create_log()
    log.timestamp = None

    repository.list_logs.return_value = [log]

    result = service.get_audit_trail()

    assert result[0]["timestamp"] is None


def test_get_failed_operations_without_timestamp(audit_service):
    service, repository, _ = audit_service

    log = create_log(
        level=LogLevel.ERROR.value,
    )
    log.timestamp = None

    repository.list_logs.return_value = [log]

    result = service.get_failed_operations()

    assert result[0]["timestamp"] is None