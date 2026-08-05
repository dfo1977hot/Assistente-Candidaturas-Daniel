"""Deterministic creation and verification of the productive SQLite schema."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from sqlalchemy import Engine, inspect

from acd.database.model_registry import EXPECTED_ORM_TABLES, ModelRegistryResult, load_models
from acd.database.schema_version import SCHEMA_VERSION
from acd.models.base import Base
from acd.observability import observed_operation

logger = logging.getLogger(__name__)


class DatabaseBootstrapError(RuntimeError):
    """Raised when model registration or schema initialization fails."""

@dataclass(frozen=True, slots=True)
class DatabaseBootstrapResult:
    registry_result: ModelRegistryResult
    physical_tables: tuple[str, ...]
    missing_tables: tuple[str, ...]
    unexpected_tables: tuple[str, ...]

class SchemaInitializer:
    def initialize(self, engine: Engine) -> None:
        with engine.begin() as connection:
            Base.metadata.create_all(bind=connection)
            current_row = connection.exec_driver_sql("PRAGMA user_version").fetchone()
            current_version = 0 if current_row is None else int(current_row[0])
            if current_version < SCHEMA_VERSION:
                connection.exec_driver_sql(f"PRAGMA user_version = {SCHEMA_VERSION}")

class DatabaseBootstrap:
    def __init__(self, initializer: SchemaInitializer | None = None) -> None:
        self._initializer = initializer or SchemaInitializer()

    def initialize(self, engine: Engine) -> DatabaseBootstrapResult:
        try:
            with observed_operation(logger, "database.bootstrap", component="database"):
                registry = load_models()
                self._initializer.initialize(engine)
                actual = frozenset(inspect(engine).get_table_names())
        except Exception as exc:
            raise DatabaseBootstrapError("Database bootstrap failed") from exc
        missing, unexpected = EXPECTED_ORM_TABLES - actual, actual - EXPECTED_ORM_TABLES
        if missing:
            raise DatabaseBootstrapError(f"Physical schema missing required tables: {sorted(missing)}")
        return DatabaseBootstrapResult(
            registry,
            tuple(sorted(actual)),
            tuple(sorted(missing)),
            tuple(sorted(unexpected)),
        )
