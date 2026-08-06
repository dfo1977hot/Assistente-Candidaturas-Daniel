"""Explicit SQLite schema version helpers."""

from __future__ import annotations

from typing import Any, Protocol

SCHEMA_VERSION = 1


class SchemaVersionConnection(Protocol):
    def execute(self, statement: str, /) -> Any: ...


def read_schema_version(connection: SchemaVersionConnection) -> int:
    """Read SQLite PRAGMA user_version from a connection-like object."""
    row = connection.execute("PRAGMA user_version").fetchone()
    if row is None:
        return 0
    return int(row[0])


def write_schema_version(connection: SchemaVersionConnection, version: int) -> int:
    """Write SQLite PRAGMA user_version and return the normalized version."""
    normalized = int(version)
    if normalized < 0:
        raise ValueError("Schema version must be non-negative")
    connection.execute(f"PRAGMA user_version = {normalized}")
    return normalized


def ensure_schema_version(
    connection: SchemaVersionConnection,
    version: int = SCHEMA_VERSION,
) -> int:
    """Ensure the connection advertises at least the requested schema version."""
    current = read_schema_version(connection)
    if current < version:
        return write_schema_version(connection, version)
    return current
