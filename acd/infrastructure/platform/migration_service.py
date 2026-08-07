"""Migration service for database schema versioning and controlled evolution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

logger = logging.getLogger(__name__)

MigrationCallback = Callable[[Any], None]


@dataclass(slots=True)
class Migration:
    """Database migration definition."""

    version: str
    description: str
    upgrade: MigrationCallback
    downgrade: MigrationCallback
    dependencies: list[str] | None = None


class MigrationService:
    """Manages database migrations."""

    __slots__ = ("migrations", "applied_migrations")

    def __init__(self) -> None:
        self.migrations: dict[str, Migration] = {}
        self.applied_migrations: list[str] = []

    def register_migration(self, migration: Migration) -> None:
        self.migrations[migration.version] = migration

    def get_applied_migrations(self) -> list[str]:
        return sorted(self.applied_migrations)

    def get_pending_migrations(self) -> list[Migration]:
        applied = set(self.applied_migrations)
        pending: list[Migration] = []
        for version in sorted(self.migrations):
            migration = self.migrations[version]
            if version in applied:
                continue
            if migration.dependencies and not all(dep in applied for dep in migration.dependencies):
                continue
            pending.append(migration)
        return pending

    def apply_migration(self, version: str, session: Any) -> bool:
        migration = self.migrations.get(version)
        if migration is None:
            return False
        try:
            migration.upgrade(session)
            self.applied_migrations.append(version)
            return True
        except Exception:
            logger.exception("Migration %s failed", version)
            return False

    def revert_migration(self, version: str, session: Any) -> bool:
        migration = self.migrations.get(version)
        if migration is None or version not in self.applied_migrations:
            return False
        try:
            migration.downgrade(session)
            self.applied_migrations.remove(version)
            return True
        except Exception:
            logger.exception("Revert migration %s failed", version)
            return False

    def apply_all_pending(self, session: Any) -> dict[str, bool]:
        return {m.version: self.apply_migration(m.version, session) for m in self.get_pending_migrations()}

    def revert_all(self, session: Any) -> dict[str, bool]:
        return {v: self.revert_migration(v, session) for v in reversed(self.get_applied_migrations())}

    def get_status(self) -> dict[str, Any]:
        pending = self.get_pending_migrations()
        return {
            "total_migrations": len(self.migrations),
            "applied_migrations": len(self.applied_migrations),
            "pending_migrations": len(pending),
            "applied_versions": self.get_applied_migrations(),
            "pending_versions": [m.version for m in pending],
        }


_service: MigrationService | None = None


def get_migration_service() -> MigrationService:
    global _service
    if _service is None:
        _service = MigrationService()
    return _service


def create_example_migrations() -> list[Migration]:
    """Create example migrations."""

    def upgrade_v1(session: Any) -> None:
        from acd.models.base import Base
        Base.metadata.create_all(session.bind)

    def downgrade_v1(session: Any) -> None:
        del session
        raise NotImplementedError("Downgrade for the initial migration is not implemented.")

    return [
        Migration(
            version="20260701_000000_initial_platform",
            description="Create initial platform tables",
            upgrade=upgrade_v1,
            downgrade=downgrade_v1,
        )
    ]
