from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from acd.application.platform.database_lifecycle import (
    BackupHashMismatchError,
    DatabaseIntegrityError,
)
from acd.database.create_database import create_database
from acd.database.local_state import sqlite_url
from tests.acceptance.conftest import build_acceptance_runtime
from tests.acceptance.test_mvp_workflow_and_persistence import _seed_mvp_flow


def test_mvp_backup_restore_round_trip_and_rejections(acceptance_runtime, monkeypatch, qtbot) -> None:
    ids = _seed_mvp_flow(acceptance_runtime)
    backup_path = acceptance_runtime.backup_dir / "mvp-backup.sqlite3"

    result = acceptance_runtime.lifecycle.create_backup(
        acceptance_runtime.database_path,
        backup_path,
    )
    assert result.integrity == "ok"
    assert result.table_count == 92
    assert backup_path.exists()
    assert result.manifest_path.exists()

    restored_workspace = acceptance_runtime.workspace.parent / "acd-mvp-restored"
    restored_database = restored_workspace / "database" / "acd-acceptance.db"
    restored_database.parent.mkdir(parents=True, exist_ok=True)
    restored_engine = create_engine(sqlite_url(restored_database), future=True)
    try:
        create_database(restored_engine)
    finally:
        restored_engine.dispose()

    restored = acceptance_runtime.lifecycle.restore_backup(
        backup_path,
        restored_database,
        expected_sha256=result.sha256,
    )
    assert restored.integrity == "ok"
    assert restored.safety_backup is not None
    assert restored.safety_backup.path.exists()

    reopened = build_acceptance_runtime(
        monkeypatch,
        qtbot,
        restored_workspace,
        database_path=restored_database,
    )
    try:
        reopened.dashboard.refresh_kpis()
        qtbot.waitUntil(lambda: not reopened.dashboard._executor.is_running)
        assert reopened.dashboard.total_companies_card.valor_label.text() == "1"
        assert reopened.dashboard.total_jobs_card.valor_label.text() == "1"
        assert reopened.dashboard.total_applications_card.valor_label.text() == "1"
        assert reopened.application_service.get_application(ids["application_id"]) is not None
    finally:
        reopened.close()

    with pytest.raises(BackupHashMismatchError):
        acceptance_runtime.lifecycle.restore_backup(
            backup_path,
            acceptance_runtime.workspace / "database" / "reject.db",
            expected_sha256="0" * 64,
        )

    corrupt_backup = acceptance_runtime.backup_dir / "corrupt.db"
    corrupt_backup.write_bytes(b"not sqlite")
    with pytest.raises(DatabaseIntegrityError):
        acceptance_runtime.lifecycle.restore_backup(
            corrupt_backup,
            acceptance_runtime.workspace / "database" / "corrupt-target.db",
        )
