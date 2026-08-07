"""Installed version entity."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class InstallationStatus(StrEnum):
    """Installation status."""

    FRESH_INSTALL = "fresh_install"
    UPGRADED = "upgraded"
    MIGRATED = "migrated"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class InstalledVersion(Base):
    """Track installed version information."""

    __tablename__ = "installed_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    current_version: Mapped[str] = mapped_column(unique=True, index=True)
    previous_version: Mapped[str | None] = mapped_column(nullable=True)
    installation_path: Mapped[str]
    installation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
    )
    last_update_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    installation_type: Mapped[str]  # FRESH_INSTALL, UPGRADED, MIGRATED
    status: Mapped[str]  # ACTIVE, DEPRECATED
    is_beta: Mapped[bool] = mapped_column(default=False)
    installation_metadata: Mapped[dict] = mapped_column(JSON, default={})  # Custom data
    system_info: Mapped[dict] = mapped_column(JSON, default={})  # OS, Python version, etc
    has_backup: Mapped[bool] = mapped_column(default=False)
    migration_completed: Mapped[bool] = mapped_column(default=True)
    rollback_available: Mapped[bool] = mapped_column(default=False)
    rollback_version: Mapped[str | None] = mapped_column(nullable=True)
    checksum: Mapped[str | None] = mapped_column(nullable=True)  # Installation integrity

    def is_active(self) -> bool:
        """Check if installation is active."""
        return self.status == InstallationStatus.ACTIVE.value

    def is_deprecated(self) -> bool:
        """Check if installation is deprecated."""
        return self.status == InstallationStatus.DEPRECATED.value

    def can_rollback(self) -> bool:
        """Check if rollback is available."""
        return self.rollback_available and self.rollback_version is not None

    def get_version_info(self) -> dict:
        """Get version information."""
        return {
            "current": self.current_version,
            "previous": self.previous_version,
            "is_beta": self.is_beta,
            "status": self.status,
        }

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "current_version": self.current_version,
            "previous_version": self.previous_version,
            "installation_path": self.installation_path,
            "installation_date": self.installation_date.isoformat(),
            "status": self.status,
            "is_beta": self.is_beta,
            "can_rollback": self.can_rollback(),
        }
