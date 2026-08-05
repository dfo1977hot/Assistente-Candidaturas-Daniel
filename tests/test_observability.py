from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import logging
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_engine

from acd.application.platform.services.audit_service import AuditService
from acd.database.create_database import create_database
from acd.observability.diagnostics import (
    DiagnosticExportExistsError,
    OperationalDiagnostics,
)
from acd.observability.logging_config import (
    DEFAULT_BACKUP_COUNT,
    close_logging,
    configure_logging,
    log_event,
    observed_operation,
    resolve_log_directory,
)
from acd.observability.operation_context import (
    bind_observation_context,
    observation_context,
)
from acd.observability.sanitization import REDACTED, sanitize_mapping, sanitize_text


@pytest.fixture(autouse=True)
def isolated_logging():
    close_logging()
    yield
    close_logging()


def test_import_has_no_log_directory_side_effect(tmp_path) -> None:
    target = tmp_path / "local"
    environment = os.environ.copy()
    environment["LOCALAPPDATA"] = str(target)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    completed = subprocess.run(
        [sys.executable, "-c", "import acd.observability.logging_config"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert not (target / "ACD" / "logs").exists()


def test_log_path_is_cwd_independent_and_override_is_explicit(monkeypatch, tmp_path) -> None:
    override = tmp_path / "logs"
    monkeypatch.chdir(tmp_path)
    first = resolve_log_directory(override)
    monkeypatch.chdir(tmp_path.parent)
    assert resolve_log_directory(override) == first == override.resolve()
    assert not override.exists()


def test_configuration_is_idempotent_structured_rotating_and_closable(tmp_path) -> None:
    path = configure_logging(
        log_directory=tmp_path, console=False, max_bytes=180, backup_count=2
    )
    second = configure_logging(log_directory=tmp_path, console=False)
    logger = logging.getLogger("acd.test")
    for index in range(12):
        log_event(logger, logging.INFO, "test.event", f"message-{index}", status="completed")
    handlers = [h for h in logging.getLogger("acd").handlers if hasattr(h, "baseFilename")]
    assert path == second == tmp_path / "acd.jsonl"
    assert len(handlers) == 1
    assert handlers[0].backupCount == 2
    assert DEFAULT_BACKUP_COUNT == 5
    close_logging()
    assert not [
        handler
        for handler in logging.getLogger("acd").handlers
        if getattr(handler, "_acd_observability_handler", False)
    ]
    (tmp_path / "acd.jsonl").unlink()


def test_json_format_contains_required_context_and_duration(tmp_path) -> None:
    path = configure_logging(log_directory=tmp_path, console=False)
    logger = logging.getLogger("acd.component")
    with bind_observation_context(correlation_id="corr-safe", operation_id="op-safe"):
        with observed_operation(logger, "workflow", component="workflow"):
            pass
    close_logging()
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [record["event_name"] for record in records] == [
        "workflow.started",
        "workflow.completed",
    ]
    assert records[-1]["correlation_id"]
    assert records[-1]["operation_id"]
    assert records[-1]["duration_ms"] >= 0
    assert {"timestamp", "level", "logger", "message", "status", "app_version"} <= records[-1].keys()


def test_context_is_restored_and_isolated_between_threads() -> None:
    before = observation_context().correlation_id
    with bind_observation_context(correlation_id="outer"):
        assert observation_context().correlation_id == "outer"
    assert observation_context().correlation_id == before

    def read_context(value: str) -> str:
        with bind_observation_context(correlation_id=value):
            return observation_context().correlation_id

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert set(executor.map(read_context, ["one", "two"])) == {"one", "two"}


def test_privacy_redaction_covers_personal_data_and_secrets(tmp_path) -> None:
    synthetic = {
        "cpf": "123.456.789-00",
        "rg": "12.345.678-9",
        "email": "person@example.test",
        "phone": "+55 (11) 99999-0000",
        "token": "synthetic-token-value",
        "api_key": "sk-SYNTHETICSECRET123",
        "password": "synthetic-password",
        "prompt": "synthetic private prompt",
        "Authorization": "Bearer synthetic-token-value",
    }
    sanitized = sanitize_mapping(synthetic)
    assert all(value == REDACTED for value in sanitized.values())

    path = configure_logging(log_directory=tmp_path, console=False)
    logger = logging.getLogger("acd.privacy")
    message = "123.456.789-00 person@example.test +55 (11) 99999-0000 sk-SYNTHETICSECRET123"
    log_event(logger, logging.ERROR, "privacy.test", message, status="failed", **synthetic)
    try:
        raise RuntimeError("password=synthetic-password")
    except RuntimeError:
        logger.exception("Authorization: Bearer synthetic-token-value")
    close_logging()
    content = path.read_text(encoding="utf-8")
    for secret in synthetic.values():
        assert str(secret) not in content
    assert "synthetic-password" not in content
    assert REDACTED in content


def test_sanitizer_truncates_and_does_not_mutate_input() -> None:
    source = {"safe": "x" * 600, "nested": {"email": "person@example.test"}}
    sanitized = sanitize_mapping(source)
    assert sanitized["safe"].endswith("…[TRUNCATED]")
    assert source["nested"]["email"] == "person@example.test"
    assert sanitize_text(source["nested"]["email"]) == REDACTED


def test_diagnostics_health_and_export_are_sanitized(tmp_path) -> None:
    data = tmp_path / "personal-user-name" / "data"
    logs = tmp_path / "personal-user-name" / "logs"
    data.mkdir(parents=True)
    logs.mkdir()
    database = data / "synthetic.db"
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    try:
        create_database(engine)
    finally:
        engine.dispose()
    service = OperationalDiagnostics()
    report = service.collect(data_directory=data, log_directory=logs, database_path=database)
    database_health = next(item for item in report["health_checks"] if item["name"] == "database")
    assert database_health["status"] == "healthy"
    assert database_health["details"]["expected_tables"] == 92
    assert database_health["details"]["found_tables"] == 92
    assert "personal-user-name" not in json.dumps(report)
    destination = tmp_path / "diagnostics.json"
    digest = service.export(report, destination)
    assert len(digest) == 64
    with pytest.raises(DiagnosticExportExistsError):
        service.export(report, destination)


def test_audit_metadata_and_identity_are_sanitized(monkeypatch) -> None:
    repository = pytest.MonkeyPatch()
    del repository
    session = object()
    service = AuditService.__new__(AuditService)
    service.session = session
    from unittest.mock import MagicMock

    service.repository = MagicMock()
    service.logger = MagicMock()
    operation = MagicMock()
    operation.__enter__.return_value = None
    operation.__exit__.return_value = None
    service.logger.operation.return_value = operation
    service.repository.create_log.return_value = type(
        "Log", (), {"id": 1, "timestamp": None}
    )()
    service.log_critical_operation(
        "backup.requested",
        "platform",
        user_id="person@example.test",
        details={"token": "synthetic-token-value", "entity_id": 42},
    )
    kwargs = service.repository.create_log.call_args.kwargs
    assert kwargs["user_id"] == REDACTED
    assert kwargs["metadata"] == {"token": REDACTED, "entity_id": 42}
