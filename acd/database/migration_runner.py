"""Controlled SQLite schema migrations for the local database."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from pathlib import Path
import sqlite3

from acd.application.platform.database_lifecycle import (
    DatabaseSourceMissingError,
    SchemaCompatibilityError,
)
from acd.database.model_registry import EXPECTED_ORM_TABLES
from acd.database.schema_version import SCHEMA_VERSION, read_schema_version, write_schema_version
from acd.infrastructure.database.sqlite_lifecycle import SQLiteDatabaseLifecycle

logger = logging.getLogger(__name__)

MigrationCallback = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True, slots=True)
class DatabaseMigration:
    """Declarative, non-destructive SQLite schema migration."""

    number: int
    name: str
    description: str
    source_version: int
    target_version: int
    upgrade: MigrationCallback
    reversible: bool = False
    affected_tables: tuple[str, ...] = ()


class DatabaseMigrationError(RuntimeError):
    """Raised when a migration plan or migration execution fails."""


class DatabaseMigrationRunner:
    """Apply ordered SQLite schema migrations with per-migration recovery."""

    def __init__(
        self,
        migrations: Iterable[DatabaseMigration] = (),
        *,
        lifecycle: SQLiteDatabaseLifecycle | None = None,
    ) -> None:
        self._lifecycle = lifecycle or SQLiteDatabaseLifecycle()
        self._migrations = tuple(sorted(migrations, key=lambda migration: migration.number))
        self._supported_version = max(
            (migration.target_version for migration in self._migrations),
            default=SCHEMA_VERSION,
        )
        self._validate_plan()

    def _validate_plan(self) -> None:
        previous_target: int | None = None
        seen_numbers: set[int] = set()
        for migration in self._migrations:
            if migration.number in seen_numbers:
                raise DatabaseMigrationError(f"Duplicate migration number: {migration.number}")
            if migration.target_version <= migration.source_version:
                raise DatabaseMigrationError(
                    f"Migration {migration.name} must advance the schema version"
                )
            if previous_target is not None and migration.source_version != previous_target:
                raise DatabaseMigrationError(
                    f"Migration {migration.name} breaks the version chain at {migration.source_version}"
                )
            previous_target = migration.target_version
            seen_numbers.add(migration.number)

    def run(self, database_path: Path, *, backup_directory: Path | None = None) -> tuple[int, ...]:
        """Apply all pending migrations for a file-backed SQLite database."""
        resolved_path = Path(database_path).expanduser().resolve()
        if not resolved_path.is_file():
            raise DatabaseSourceMissingError("Database source does not exist")

        applied: list[int] = []
        current_version = self._read_version(resolved_path)
        if current_version == 0:
            current_version = self._normalize_legacy_baseline(resolved_path)
        if current_version > self._supported_version:
            raise SchemaCompatibilityError(
                f"Database schema version {current_version} is newer than supported {self._supported_version}"
            )
        for migration in self._pending_migrations(current_version):
            backup_result = self._backup_before_migration(
                resolved_path,
                migration,
                current_version=current_version,
                backup_directory=backup_directory,
            )
            try:
                with closing(sqlite3.connect(resolved_path)) as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    migration.upgrade(connection)
                    write_schema_version(connection, migration.target_version)
                    connection.commit()
            except Exception:
                if backup_result is not None:
                    self._lifecycle.restore_backup(
                        backup_result.path,
                        resolved_path,
                        expected_sha256=backup_result.sha256,
                        maximum_schema_version=self._supported_version,
                    )
                raise
            current_version = migration.target_version
            applied.append(migration.number)
        return tuple(applied)

    def _pending_migrations(self, current_version: int) -> tuple[DatabaseMigration, ...]:
        pending: list[DatabaseMigration] = []
        expected_version = current_version
        for migration in self._migrations:
            if migration.target_version <= current_version:
                continue
            if migration.source_version != expected_version:
                raise DatabaseMigrationError(
                    f"Missing migration for version {expected_version} before {migration.name}"
                )
            pending.append(migration)
            expected_version = migration.target_version
        return tuple(pending)

    def _backup_before_migration(
        self,
        database_path: Path,
        migration: DatabaseMigration,
        *,
        current_version: int,
        backup_directory: Path | None,
    ):
        backup_root = backup_directory or database_path.parent / "backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        backup_path = backup_root / (
            f"{database_path.stem}-schema{current_version:04d}-"
            f"before-{migration.target_version:04d}-{stamp}{database_path.suffix}"
        )
        return self._lifecycle.create_backup(database_path, backup_path)

    @staticmethod
    def _read_version(database_path: Path) -> int:
        with closing(sqlite3.connect(database_path)) as connection:
            return read_schema_version(connection)

    @staticmethod
    def _normalize_legacy_baseline(database_path: Path) -> int:
        uri = f"file:{database_path.as_posix()}?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            tables = frozenset(
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
                if not str(row[0]).startswith("sqlite_")
            )
            missing = EXPECTED_ORM_TABLES - tables
            if missing:
                raise SchemaCompatibilityError(
                    "Legacy schema version 0 requires the full 92-table baseline"
                )
        return 1
