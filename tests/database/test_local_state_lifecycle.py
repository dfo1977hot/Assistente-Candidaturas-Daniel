from __future__ import annotations

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect, text

from acd.application.platform.database_lifecycle import (
    BackupDestinationExistsError,
    BackupHashMismatchError,
    DatabaseIntegrityError,
    SchemaCompatibilityError,
)
from acd.database.create_database import create_database
from acd.database.local_state import resolve_database_path
from acd.database.model_registry import EXPECTED_ORM_TABLES
from acd.infrastructure.database.sqlite_lifecycle import SQLiteDatabaseLifecycle


def _create_database(path: Path) -> None:
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        create_database(engine)
    finally:
        engine.dispose()


def test_path_resolution_is_cwd_independent_and_supports_explicit_override(
    monkeypatch, tmp_path
) -> None:
    override = tmp_path / "state" / "test.db"
    monkeypatch.chdir(tmp_path)
    first = resolve_database_path(override)
    monkeypatch.chdir(tmp_path.parent)
    second = resolve_database_path(override)
    assert first == second == override.resolve()
    assert not override.exists()


def test_environment_override_is_explicit_and_has_no_import_side_effect(tmp_path) -> None:
    target = tmp_path / "not-created" / "state.db"
    script = (
        "from acd.database.local_state import resolve_database_path; "
        "print(resolve_database_path())"
    )
    environment = os.environ.copy()
    environment.update({"ACD_DATABASE_PATH": str(target), "LOCALAPPDATA": str(tmp_path)})
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert Path(completed.stdout.strip()) == target.resolve()
    assert not target.parent.exists()


def test_clean_bootstrap_creates_parent_and_preserves_data_and_extra_table(tmp_path) -> None:
    path = tmp_path / "new" / "acd.db"
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        create_database(engine)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO companies "
                    "(name, segment, city, state, country, company_size, created_at, updated_at) "
                    "VALUES ('Synthetic', '', '', '', '', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                )
            )
            connection.execute(text("CREATE TABLE local_extension (id INTEGER PRIMARY KEY)"))
        create_database(engine)
        tables = set(inspect(engine).get_table_names())
        assert EXPECTED_ORM_TABLES <= tables
        assert "local_extension" in tables
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM companies")) == 1
    finally:
        engine.dispose()


def test_backup_uses_sqlite_api_writes_manifest_hash_and_refuses_overwrite(tmp_path) -> None:
    source = tmp_path / "source.db"
    backup = tmp_path / "backups" / "acd-backup.sqlite3"
    _create_database(source)
    lifecycle = SQLiteDatabaseLifecycle()
    result = lifecycle.create_backup(source, backup)
    assert result.integrity == "ok"
    assert result.table_count == 92
    assert result.sha256 == hashlib.sha256(backup.read_bytes()).hexdigest()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["sha256"] == result.sha256
    assert manifest["schema_table_count"] == 92
    with pytest.raises(BackupDestinationExistsError):
        lifecycle.create_backup(source, backup)


def test_backup_is_consistent_while_source_uses_wal(tmp_path) -> None:
    source = tmp_path / "wal-source.db"
    backup = tmp_path / "wal-backup.sqlite3"
    _create_database(source)
    with closing(sqlite3.connect(source)) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE local_extension (id INTEGER PRIMARY KEY)")
        connection.execute("INSERT INTO local_extension VALUES (1)")
        connection.commit()
        result = SQLiteDatabaseLifecycle().create_backup(source, backup)
    assert result.table_count == 93
    with closing(sqlite3.connect(backup)) as connection:
        assert connection.execute("SELECT count(*) FROM local_extension").fetchone()[0] == 1


def test_restore_validates_hash_and_preserves_current_database(tmp_path) -> None:
    original = tmp_path / "original.db"
    destination = tmp_path / "destination.db"
    backup = tmp_path / "backup.sqlite3"
    _create_database(original)
    _create_database(destination)
    lifecycle = SQLiteDatabaseLifecycle()
    created = lifecycle.create_backup(original, backup)
    restored = lifecycle.restore_backup(
        backup, destination, expected_sha256=created.sha256
    )
    assert restored.integrity == "ok"
    assert restored.table_count == 92
    assert restored.safety_backup is not None
    assert restored.safety_backup.path.exists()
    assert restored.path.exists()


def test_restore_rejects_hash_corruption_and_incompatible_schema(tmp_path) -> None:
    lifecycle = SQLiteDatabaseLifecycle()
    valid = tmp_path / "valid.db"
    _create_database(valid)
    with pytest.raises(BackupHashMismatchError):
        lifecycle.restore_backup(valid, tmp_path / "target.db", expected_sha256="0" * 64)

    incompatible = tmp_path / "incompatible.db"
    with closing(sqlite3.connect(incompatible)) as connection:
        connection.execute("CREATE TABLE only_one (id INTEGER PRIMARY KEY)")
    with pytest.raises(SchemaCompatibilityError):
        lifecycle.restore_backup(incompatible, tmp_path / "target.db")


def test_restore_rejects_corrupt_database_without_touching_destination(tmp_path) -> None:
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"not sqlite")
    destination = tmp_path / "destination.db"
    destination.write_bytes(b"preserved")
    with pytest.raises(DatabaseIntegrityError):
        SQLiteDatabaseLifecycle().restore_backup(corrupt, destination)
    assert destination.read_bytes() == b"preserved"
