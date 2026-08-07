"""Application contracts for safe local database lifecycle operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol


class DatabaseLifecycleError(RuntimeError):
    """Base error for a lifecycle operation."""


class DatabaseSourceMissingError(DatabaseLifecycleError):
    """The requested database or backup does not exist."""


class BackupDestinationExistsError(DatabaseLifecycleError):
    """A backup destination would be overwritten."""


class DatabaseIntegrityError(DatabaseLifecycleError):
    """SQLite reported an invalid or corrupt database."""


class SchemaCompatibilityError(DatabaseLifecycleError):
    """The database lacks required schema elements."""


class BackupHashMismatchError(DatabaseLifecycleError):
    """The backup does not match its declared SHA-256 hash."""


class DatabaseBusyError(DatabaseLifecycleError):
    """SQLite remained busy or locked after the bounded retry policy."""


@dataclass(frozen=True, slots=True)
class BackupResult:
    path: Path
    manifest_path: Path
    created_at: datetime
    sha256: str
    size_bytes: int
    table_count: int
    integrity: str
    application_version: str


@dataclass(frozen=True, slots=True)
class RestoreResult:
    path: Path
    safety_backup: BackupResult | None
    restored_at: datetime
    sha256: str
    table_count: int
    integrity: str


class DatabaseLifecycle(Protocol):
    def create_backup(self, source: Path, destination: Path) -> BackupResult: ...

    def restore_backup(
        self,
        backup: Path,
        destination: Path,
        *,
        expected_sha256: str | None = None,
        maximum_schema_version: int | None = None,
    ) -> RestoreResult: ...
