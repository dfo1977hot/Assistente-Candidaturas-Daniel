"""Consistent SQLite backup, validation, and atomic restore."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import closing
from datetime import UTC, datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import time

from acd.application.platform.database_lifecycle import (
    BackupDestinationExistsError,
    BackupHashMismatchError,
    BackupResult,
    DatabaseBusyError,
    DatabaseIntegrityError,
    DatabaseSourceMissingError,
    RestoreResult,
    SchemaCompatibilityError,
)
from acd.database.model_registry import EXPECTED_ORM_TABLES
from acd.database.schema_version import SCHEMA_VERSION
from acd.observability import log_event, observed_operation
from acd.resilience import RetryPolicy, execute_with_retry
from acd.security.secure_paths import validate_filename
from acd.version import get_version

logger = logging.getLogger(__name__)
_DATABASE_EXTENSIONS = frozenset({".db", ".sqlite", ".sqlite3", ".bak"})
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


class SQLiteDatabaseLifecycle:
    """Operate only on explicit paths using SQLite's online-backup API."""

    def __init__(
        self,
        *,
        busy_timeout_seconds: float = 1.0,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if busy_timeout_seconds <= 0:
            raise ValueError("SQLite busy timeout must be positive")
        self._busy_timeout_seconds = busy_timeout_seconds
        self._sleeper = sleeper

    def create_backup(self, source: Path, destination: Path) -> BackupResult:
        with observed_operation(logger, "database.backup", component="sqlite"):
            return self._create_backup(source, destination)

    def _create_backup(self, source: Path, destination: Path) -> BackupResult:
        source = source.expanduser().resolve()
        destination = destination.expanduser().resolve()
        validate_filename(
            source.name, allowed_extensions=_DATABASE_EXTENSIONS, reject_double_extension=False
        )
        validate_filename(
            destination.name, allowed_extensions=_DATABASE_EXTENSIONS, reject_double_extension=False
        )
        if not source.is_file():
            raise DatabaseSourceMissingError("Database source does not exist")
        manifest_path = destination.with_suffix(destination.suffix + ".json")
        if destination.exists() or manifest_path.exists():
            raise BackupDestinationExistsError("Backup destination already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._copy_database(source, destination)
            integrity, tables, schema_version = self._validate(destination)
            digest = self._sha256(destination)
            created_at = datetime.now(UTC)
            result = BackupResult(
                path=destination,
                manifest_path=manifest_path,
                created_at=created_at,
                sha256=digest,
                size_bytes=destination.stat().st_size,
                table_count=len(tables),
                integrity=integrity,
                application_version=get_version(),
            )
            manifest = {
                "application_version": result.application_version,
                "created_at": created_at.isoformat(),
                "integrity": integrity,
                "schema_version": schema_version,
                "schema_table_count": len(tables),
                "sha256": digest,
                "size_bytes": result.size_bytes,
            }
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            return result
        except Exception as error:
            if destination.exists():
                destination.unlink()
            if manifest_path.exists():
                manifest_path.unlink()
            log_event(
                logger,
                logging.ERROR,
                "backup.failed",
                "Database backup failed",
                component="sqlite",
                status="failed",
                error_type=type(error).__name__,
            )
            raise

    def restore_backup(
        self,
        backup: Path,
        destination: Path,
        *,
        expected_sha256: str | None = None,
        maximum_schema_version: int | None = None,
    ) -> RestoreResult:
        with observed_operation(logger, "database.restore", component="sqlite"):
            return self._restore_backup(
                backup,
                destination,
                expected_sha256=expected_sha256,
                maximum_schema_version=maximum_schema_version,
            )

    def _restore_backup(
        self,
        backup: Path,
        destination: Path,
        *,
        expected_sha256: str | None = None,
        maximum_schema_version: int | None = None,
    ) -> RestoreResult:
        backup = backup.expanduser().resolve()
        destination = destination.expanduser().resolve()
        validate_filename(
            backup.name, allowed_extensions=_DATABASE_EXTENSIONS, reject_double_extension=False
        )
        validate_filename(
            destination.name, allowed_extensions=_DATABASE_EXTENSIONS, reject_double_extension=False
        )
        if not backup.is_file():
            raise DatabaseSourceMissingError("Backup source does not exist")
        actual_hash = self._sha256(backup)
        if expected_sha256 is not None and (
            not _SHA256.fullmatch(expected_sha256) or actual_hash != expected_sha256.lower()
        ):
            raise BackupHashMismatchError("Backup SHA-256 mismatch")
        integrity, tables, schema_version = self._validate(backup)
        ceiling = SCHEMA_VERSION if maximum_schema_version is None else maximum_schema_version
        if schema_version > ceiling:
            raise SchemaCompatibilityError(
                f"Backup schema version {schema_version} is newer than supported {ceiling}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        safety = None
        if destination.exists():
            safety_path = destination.with_name(
                f"{destination.stem}.pre-restore-{stamp}{destination.suffix}"
            )
            safety = self._create_backup(destination, safety_path)

        temporary_path: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{destination.stem}-restore-",
                suffix=destination.suffix,
                dir=destination.parent,
            )
            os.close(descriptor)
            temporary_path = Path(temporary_name)
            temporary_path.unlink()
            self._copy_database(backup, temporary_path)
            self._validate(temporary_path)
            os.replace(temporary_path, destination)
            temporary_path = None
        except Exception as error:
            log_event(
                logger,
                logging.ERROR,
                "restore.rolled_back",
                "Restore failed before atomic promotion; destination was preserved",
                component="sqlite",
                status="rolled_back",
                error_type=type(error).__name__,
            )
            raise
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

        return RestoreResult(
            path=destination,
            safety_backup=safety,
            restored_at=datetime.now(UTC),
            sha256=self._sha256(destination),
            table_count=len(tables),
            integrity=integrity,
        )

    def _copy_database(self, source: Path, destination: Path) -> None:
        """Copy committed SQLite state with a short retry for busy/locked only."""

        def copy_once() -> None:
            with closing(
                sqlite3.connect(source, timeout=self._busy_timeout_seconds)
            ) as source_connection:
                with closing(
                    sqlite3.connect(destination, timeout=self._busy_timeout_seconds)
                ) as destination_connection:
                    source_connection.backup(destination_connection)

        def retryable(error: Exception) -> bool:
            return isinstance(error, sqlite3.OperationalError) and any(
                marker in str(error).lower() for marker in ("busy", "locked")
            )

        def retry_event(attempt: int, delay: float, error: Exception) -> None:
            log_event(
                logger,
                logging.WARNING,
                "operation.retry_scheduled",
                "SQLite operation retry scheduled",
                component="sqlite",
                status="retrying",
                attempt=attempt,
                retry_after=round(delay, 3),
                error_type=type(error).__name__,
            )

        try:
            execute_with_retry(
                copy_once,
                policy=RetryPolicy(
                    max_attempts=3,
                    base_delay_seconds=0.05,
                    maximum_delay_seconds=0.2,
                    jitter_seconds=0.0,
                    deadline_seconds=max(1.0, self._busy_timeout_seconds * 4),
                ),
                is_retryable=retryable,
                is_idempotent=True,
                sleeper=self._sleeper,
                on_retry=retry_event,
            )
        except sqlite3.OperationalError as error:
            if retryable(error):
                raise DatabaseBusyError("SQLite remained busy after bounded retries") from error
            raise

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _validate(path: Path) -> tuple[str, frozenset[str], int]:
        try:
            uri = f"file:{path.as_posix()}?mode=ro"
            with closing(sqlite3.connect(uri, uri=True)) as connection:
                integrity_row = connection.execute("PRAGMA integrity_check").fetchone()
                integrity = "" if integrity_row is None else str(integrity_row[0])
                if integrity.lower() != "ok":
                    raise DatabaseIntegrityError("SQLite integrity check failed")
                version_row = connection.execute("PRAGMA user_version").fetchone()
                schema_version = 0 if version_row is None else int(version_row[0])
                tables = frozenset(
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                    if not str(row[0]).startswith("sqlite_")
                )
        except DatabaseIntegrityError:
            raise
        except sqlite3.DatabaseError as exc:
            raise DatabaseIntegrityError("SQLite database cannot be read") from exc
        missing = EXPECTED_ORM_TABLES - tables
        if missing:
            raise SchemaCompatibilityError(
                f"Database schema is missing {len(missing)} required table(s)"
            )
        return integrity, tables, schema_version
