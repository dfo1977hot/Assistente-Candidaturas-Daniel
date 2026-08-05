from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3

import pytest
from sqlalchemy import create_engine, text

from acd.application.platform.database_lifecycle import SchemaCompatibilityError
from acd.database.create_database import create_database
from acd.database.database_bootstrap import DatabaseBootstrap
from acd.database.local_state import (
    LEGACY_DATABASE_PATH,
    ensure_non_productive_database_path,
    is_productive_database_path,
    official_database_path,
)
from acd.database.migration_runner import (
    DatabaseMigration,
    DatabaseMigrationError,
    DatabaseMigrationRunner,
)
from acd.database.schema_version import read_schema_version
from acd.infrastructure.database.sqlite_lifecycle import SQLiteDatabaseLifecycle

ROOT = Path(__file__).resolve().parents[2]


def _create_engine(path: Path):
    return create_engine(f"sqlite:///{path.as_posix()}")


def _bootstrap_database(path: Path) -> None:
    engine = _create_engine(path)
    try:
        create_database(engine)
    finally:
        engine.dispose()


def test_guard_rejects_productive_paths_and_accepts_safe_overrides(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(ROOT)

    legacy_relative = Path("data/database/acd.db")
    official = official_database_path(environ={"LOCALAPPDATA": str(tmp_path)})
    safe_path = tmp_path / "isolated" / "test.db"

    assert is_productive_database_path(LEGACY_DATABASE_PATH)
    assert is_productive_database_path(legacy_relative)
    assert is_productive_database_path(official, environ={"LOCALAPPDATA": str(tmp_path)})
    assert ensure_non_productive_database_path(safe_path) == safe_path.resolve()

    with pytest.raises(ValueError, match="productive database path"):
        ensure_non_productive_database_path(LEGACY_DATABASE_PATH)
    with pytest.raises(ValueError, match="productive database path"):
        ensure_non_productive_database_path(legacy_relative)
    with pytest.raises(ValueError, match="productive database path"):
        ensure_non_productive_database_path(
            official,
            environ={"LOCALAPPDATA": str(tmp_path)},
        )


def test_guard_detects_symlinks_when_supported(tmp_path) -> None:
    link = tmp_path / "legacy-link.db"
    try:
        link.symlink_to(LEGACY_DATABASE_PATH)
    except (AttributeError, NotImplementedError, OSError):
        pytest.skip("Symlinks are not available in this environment")

    assert is_productive_database_path(link)
    with pytest.raises(ValueError, match="productive database path"):
        ensure_non_productive_database_path(link)


def test_bootstrap_promotes_schema_version(tmp_path) -> None:
    engine = _create_engine(tmp_path / "bootstrap.db")
    try:
        result = DatabaseBootstrap().initialize(engine)
        with engine.connect() as connection:
            assert connection.scalar(text("PRAGMA user_version")) == 1
        assert len(result.physical_tables) == 92
    finally:
        engine.dispose()


def test_zero_version_requires_full_legacy_baseline_before_migration(tmp_path) -> None:
    source = tmp_path / "legacy-zero.db"
    _bootstrap_database(source)
    with closing(sqlite3.connect(source)) as connection:
        connection.execute("CREATE TABLE legacy_extension (id INTEGER PRIMARY KEY)")
        connection.execute("PRAGMA user_version = 0")
        connection.commit()

    runner = DatabaseMigrationRunner(
        [
            DatabaseMigration(
                number=1,
                name="legacy-zero-to-two",
                description="Promote the legacy baseline to the next schema version",
                source_version=1,
                target_version=2,
                upgrade=lambda connection: connection.execute(
                    "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY)"
                ),
                affected_tables=("migration_probe",),
            )
        ]
    )

    assert runner.run(source) == (1,)
    with closing(sqlite3.connect(source)) as connection:
        assert read_schema_version(connection) == 2
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='migration_probe'"
        ).fetchone() is not None
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='legacy_extension'"
        ).fetchone() is not None


def test_zero_version_without_full_baseline_is_rejected(tmp_path) -> None:
    source = tmp_path / "empty-zero.db"
    with closing(sqlite3.connect(source)) as connection:
        connection.execute("PRAGMA user_version = 0")
        connection.commit()

    runner = DatabaseMigrationRunner()
    with pytest.raises(SchemaCompatibilityError, match="Legacy schema version 0"):
        runner.run(source)


def test_runtime_bootstrap_sets_schema_version_and_is_manifested(tmp_path) -> None:
    source = tmp_path / "runtime.db"
    _bootstrap_database(source)
    with closing(sqlite3.connect(source)) as connection:
        assert read_schema_version(connection) == 1

    lifecycle = SQLiteDatabaseLifecycle()
    backup = tmp_path / "backups" / "runtime.sqlite3"
    result = lifecycle.create_backup(source, backup)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1


def test_migration_runner_noops_on_current_version(tmp_path) -> None:
    source = tmp_path / "current.db"
    _bootstrap_database(source)
    with closing(sqlite3.connect(source)) as connection:
        connection.execute("PRAGMA user_version = 2")
        connection.commit()

    runner = DatabaseMigrationRunner(
        [
            DatabaseMigration(
                number=1,
                name="current-version",
                description="Already at the supported version",
                source_version=1,
                target_version=2,
                upgrade=lambda connection: connection.execute(
                    "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY)"
                ),
            )
        ]
    )

    assert runner.run(source) == ()
    with closing(sqlite3.connect(source)) as connection:
        assert read_schema_version(connection) == 2
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='migration_probe'"
        ).fetchone() is None


def test_backup_records_schema_version_for_future_schema(tmp_path) -> None:
    source = tmp_path / "future.db"
    _bootstrap_database(source)
    with closing(sqlite3.connect(source)) as connection:
        connection.execute("PRAGMA user_version = 2")
        connection.commit()

    lifecycle = SQLiteDatabaseLifecycle()
    result = lifecycle.create_backup(source, tmp_path / "future.sqlite3")
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 2


def test_restore_rejects_future_schema_version(tmp_path) -> None:
    backup = tmp_path / "future-backup.db"
    _bootstrap_database(backup)
    with closing(sqlite3.connect(backup)) as connection:
        connection.execute("PRAGMA user_version = 2")
        connection.commit()

    lifecycle = SQLiteDatabaseLifecycle()
    with pytest.raises(SchemaCompatibilityError, match="newer than supported"):
        lifecycle.restore_backup(backup, tmp_path / "restored.db")


def test_migration_runner_applies_a_successful_migration(tmp_path) -> None:
    source = tmp_path / "migration-success.db"
    _bootstrap_database(source)

    runner = DatabaseMigrationRunner(
        [
            DatabaseMigration(
                number=1,
                name="add-migration-probe",
                description="Create a synthetic table during version 1->2",
                source_version=1,
                target_version=2,
                upgrade=lambda connection: connection.execute(
                    "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY)"
                ),
                affected_tables=("migration_probe",),
            )
        ]
    )

    assert runner.run(source) == (1,)
    with closing(sqlite3.connect(source)) as connection:
        assert read_schema_version(connection) == 2
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='migration_probe'"
        ).fetchone() is not None


def test_migration_runner_leaves_prior_successful_migrations_committed_after_failure(
    tmp_path,
) -> None:
    source = tmp_path / "migration-lot.db"
    _bootstrap_database(source)

    migrations = [
        DatabaseMigration(
            number=1,
            name="create-migration-probe",
            description="Create a probe table",
            source_version=1,
            target_version=2,
            upgrade=lambda connection: connection.execute(
                "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY)"
            ),
            affected_tables=("migration_probe",),
        ),
        DatabaseMigration(
            number=2,
            name="fail-after-probe",
            description="Fail after the first migration is committed",
            source_version=2,
            target_version=3,
            upgrade=lambda connection: (_ for _ in ()).throw(RuntimeError("synthetic")),
            affected_tables=("migration_probe",),
        ),
    ]

    runner = DatabaseMigrationRunner(migrations)
    with pytest.raises(RuntimeError, match="synthetic"):
        runner.run(source)

    with closing(sqlite3.connect(source)) as connection:
        assert read_schema_version(connection) == 2
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='migration_probe'"
        ).fetchone() is not None


def test_migration_runner_rejects_duplicate_numbers() -> None:
    migration = DatabaseMigration(
        number=1,
        name="duplicate-number",
        description="Duplicate numbering",
        source_version=1,
        target_version=2,
        upgrade=lambda _connection: None,
    )

    with pytest.raises(DatabaseMigrationError, match="Duplicate migration number"):
        DatabaseMigrationRunner([migration, migration])


def test_migration_runner_rejects_lacuna_in_version_chain() -> None:
    migrations = [
        DatabaseMigration(
            number=1,
            name="first",
            description="First transition",
            source_version=1,
            target_version=2,
            upgrade=lambda _connection: None,
        ),
        DatabaseMigration(
            number=2,
            name="gap",
            description="Missing the required 2->3 transition",
            source_version=4,
            target_version=5,
            upgrade=lambda _connection: None,
        ),
    ]

    with pytest.raises(DatabaseMigrationError, match="breaks the version chain"):
        DatabaseMigrationRunner(migrations)


def test_migration_runner_rejects_non_advancing_target_version() -> None:
    migration = DatabaseMigration(
        number=1,
        name="flat",
        description="No version advance",
        source_version=1,
        target_version=1,
        upgrade=lambda _connection: None,
    )

    with pytest.raises(DatabaseMigrationError, match="must advance the schema version"):
        DatabaseMigrationRunner([migration])


def test_migration_runner_rejects_future_version_database(tmp_path) -> None:
    source = tmp_path / "future.db"
    _bootstrap_database(source)
    with closing(sqlite3.connect(source)) as connection:
        connection.execute("PRAGMA user_version = 3")
        connection.commit()

    runner = DatabaseMigrationRunner(
        [
            DatabaseMigration(
                number=1,
                name="current",
                description="Current supported migration",
                source_version=1,
                target_version=2,
                upgrade=lambda connection: connection.execute(
                    "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY)"
                ),
            )
        ]
    )

    with pytest.raises(SchemaCompatibilityError, match="newer than supported"):
        runner.run(source)


def test_migration_runner_restores_backup_when_upgrade_fails(tmp_path) -> None:
    source = tmp_path / "migration-failure.db"
    _bootstrap_database(source)

    def upgrade(connection: sqlite3.Connection) -> None:
        connection.execute("CREATE TABLE migration_probe (id INTEGER PRIMARY KEY)")
        raise RuntimeError("synthetic")

    runner = DatabaseMigrationRunner(
        [
            DatabaseMigration(
                number=1,
                name="failing-migration",
                description="Create a synthetic table and fail",
                source_version=1,
                target_version=2,
                upgrade=upgrade,
                affected_tables=("migration_probe",),
            )
        ]
    )

    with pytest.raises(RuntimeError, match="synthetic"):
        runner.run(source)

    with closing(sqlite3.connect(source)) as connection:
        assert read_schema_version(connection) == 1
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='migration_probe'"
        ).fetchone() is None
