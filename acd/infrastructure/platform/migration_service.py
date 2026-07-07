"""Migration service for database schema versioning and controlled evolution."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class Migration:
    """Database migration definition."""

    version: str  # Format: YYYYMMDD_HHMMSS_name
    description: str
    upgrade: Callable  # Function to upgrade
    downgrade: Callable  # Function to downgrade
    dependencies: list[str] | None = None


class MigrationService:
    """Manages database migrations."""

    def __init__(self) -> None:
        """Initialize migration service."""
        self.migrations: dict[str, Migration] = {}
        self.applied_migrations: list[str] = []

    def register_migration(self, migration: Migration) -> None:
        """Register a migration.

        Args:
            migration: Migration to register
        """
        self.migrations[migration.version] = migration

    def get_applied_migrations(self) -> list[str]:
        """Get list of applied migrations.

        Returns:
            Applied migration versions
        """
        return sorted(self.applied_migrations)

    def get_pending_migrations(self) -> list[Migration]:
        """Get list of pending migrations.

        Returns:
            Pending migrations in order
        """
        applied_set = set(self.applied_migrations)
        pending = []

        # Sort by version
        for version in sorted(self.migrations.keys()):
            if version not in applied_set:
                migration = self.migrations[version]
                # Check dependencies
                if migration.dependencies:
                    for dep in migration.dependencies:
                        if dep not in applied_set:
                            continue  # Skip if dependency not met
                pending.append(migration)

        return pending

    def apply_migration(self, version: str, session) -> bool:
        """Apply a migration.

        Args:
            version: Migration version
            session: Database session

        Returns:
            True if successful
        """
        if version not in self.migrations:
            return False

        migration = self.migrations[version]

        try:
            migration.upgrade(session)
            self.applied_migrations.append(version)
            return True
        except Exception as e:
            print(f"Migration {version} failed: {str(e)}")
            return False

    def revert_migration(self, version: str, session) -> bool:
        """Revert a migration.

        Args:
            version: Migration version
            session: Database session

        Returns:
            True if successful
        """
        if version not in self.migrations or version not in self.applied_migrations:
            return False

        migration = self.migrations[version]

        try:
            migration.downgrade(session)
            self.applied_migrations.remove(version)
            return True
        except Exception as e:
            print(f"Revert migration {version} failed: {str(e)}")
            return False

    def apply_all_pending(self, session) -> dict[str, bool]:
        """Apply all pending migrations.

        Args:
            session: Database session

        Returns:
            Results per migration
        """
        results = {}
        for migration in self.get_pending_migrations():
            results[migration.version] = self.apply_migration(migration.version, session)

        return results

    def revert_all(self, session) -> dict[str, bool]:
        """Revert all applied migrations (in reverse order).

        Args:
            session: Database session

        Returns:
            Results per migration
        """
        results = {}
        for version in reversed(self.get_applied_migrations()):
            results[version] = self.revert_migration(version, session)

        return results

    def get_status(self) -> dict[str, Any]:
        """Get migration status.

        Returns:
            Status information
        """
        return {
            "total_migrations": len(self.migrations),
            "applied_migrations": len(self.applied_migrations),
            "pending_migrations": len(self.get_pending_migrations()),
            "applied_versions": self.get_applied_migrations(),
            "pending_versions": [m.version for m in self.get_pending_migrations()],
        }


# Global service instance
_service: MigrationService | None = None


def get_migration_service() -> MigrationService:
    """Get global migration service instance.

    Returns:
        Migration service
    """
    global _service
    if _service is None:
        _service = MigrationService()
    return _service


# Example migrations for platform
def create_example_migrations() -> list[Migration]:
    """Create example migrations.

    Returns:
        List of example migrations
    """

    def upgrade_v1(session):
        """Create initial platform tables."""
        from acd.models.base import Base

        Base.metadata.create_all(session.bind)

    def downgrade_v1(session):
        """Drop platform tables."""
        pass  # Implement if needed

    return [
        Migration(
            version="20260701_000000_initial_platform",
            description="Create initial platform tables",
            upgrade=upgrade_v1,
            downgrade=downgrade_v1,
        ),
    ]
