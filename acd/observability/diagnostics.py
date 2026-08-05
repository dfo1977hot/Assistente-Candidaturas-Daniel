"""Sanitized, local and explicitly exported operational diagnostics."""

from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import sqlite3
import sys
import time
from typing import Any

from acd.database.model_registry import EXPECTED_ORM_TABLES
from acd.version import get_version

_REPORT_TOP_LEVEL_KEYS = frozenset(
    {"schema_version", "generated_at", "application", "runtime", "paths", "health_checks"}
)
_FORBIDDEN_DIAGNOSTIC_KEYS = (
    "secret",
    "password",
    "token",
    "authorization",
    "cookie",
    "prompt",
    "response",
    "record",
    "environment",
)


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    name: str
    status: str
    message: str
    duration_ms: float
    details: dict[str, Any]


class DiagnosticExportExistsError(RuntimeError):
    """A diagnostic export would overwrite existing evidence."""


def _path_label(path: Path) -> str:
    return path.name or "root"


class OperationalDiagnostics:
    """Generate support-safe facts without reading database records."""

    def collect(
        self,
        *,
        data_directory: Path,
        log_directory: Path,
        database_path: Path | None = None,
    ) -> dict[str, Any]:
        checks = [
            self._directory_check("data_directory", data_directory),
            self._directory_check("log_directory", log_directory),
        ]
        if database_path is not None:
            checks.append(self._database_check(database_path))
        return {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "application": {
                "version": get_version(),
                "entry_point": "acd.desktop:main",
            },
            "runtime": {
                "python": platform.python_version(),
                "platform": platform.system(),
                "architecture": platform.machine(),
                "executable_kind": Path(sys.executable).name,
            },
            "paths": {
                "data": _path_label(data_directory),
                "logs": _path_label(log_directory),
                "database": _path_label(database_path) if database_path else None,
            },
            "health_checks": [asdict(check) for check in checks],
        }

    def export(self, report: dict[str, Any], destination: Path) -> str:
        self._validate_report(report)
        destination = destination.expanduser().resolve()
        if destination.exists():
            raise DiagnosticExportExistsError("Diagnostic destination already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        destination.write_text(payload, encoding="utf-8")
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _validate_report(report: dict[str, Any]) -> None:
        if set(report) != _REPORT_TOP_LEVEL_KEYS:
            raise ValueError("Diagnostic report does not match the safe schema")

        def inspect(value: Any) -> None:
            if isinstance(value, dict):
                for key, nested in value.items():
                    lowered = str(key).lower()
                    if any(forbidden in lowered for forbidden in _FORBIDDEN_DIAGNOSTIC_KEYS):
                        raise ValueError("Diagnostic report contains a forbidden field")
                    inspect(nested)
            elif isinstance(value, list):
                for nested in value:
                    inspect(nested)
            elif isinstance(value, str) and len(value) > 1024:
                raise ValueError("Diagnostic report contains an oversized value")

        inspect(report)

    @staticmethod
    def _directory_check(name: str, path: Path) -> HealthCheckResult:
        start = time.perf_counter()
        exists = path.exists()
        writable = exists and os.access(path, os.W_OK)
        status = "healthy" if writable else "degraded" if not exists else "unhealthy"
        return HealthCheckResult(
            name=name,
            status=status,
            message="Directory is writable" if writable else "Directory is not writable",
            duration_ms=round((time.perf_counter() - start) * 1000, 3),
            details={"exists": exists, "writable": writable, "label": _path_label(path)},
        )

    @staticmethod
    def _database_check(path: Path) -> HealthCheckResult:
        start = time.perf_counter()
        if not path.is_file():
            return HealthCheckResult(
                "database",
                "unknown",
                "Database is absent",
                round((time.perf_counter() - start) * 1000, 3),
                {"exists": False, "label": _path_label(path)},
            )
        try:
            uri = f"file:{path.resolve().as_posix()}?mode=ro"
            with closing(sqlite3.connect(uri, uri=True)) as connection:
                quick = str(connection.execute("PRAGMA quick_check").fetchone()[0])
                tables = frozenset(
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                    if not str(row[0]).startswith("sqlite_")
                )
            missing = EXPECTED_ORM_TABLES - tables
            status = "healthy" if quick.lower() == "ok" and not missing else "unhealthy"
            message = "Database health check passed" if status == "healthy" else "Database health check failed"
            details = {
                "exists": True,
                "size_bytes": path.stat().st_size,
                "quick_check": quick.lower(),
                "expected_tables": len(EXPECTED_ORM_TABLES),
                "found_tables": len(tables),
                "missing_tables": len(missing),
                "label": _path_label(path),
            }
        except sqlite3.DatabaseError:
            status, message = "unhealthy", "Database cannot be read"
            details = {"exists": True, "label": _path_label(path)}
        return HealthCheckResult(
            "database",
            status,
            message,
            round((time.perf_counter() - start) * 1000, 3),
            details,
        )
