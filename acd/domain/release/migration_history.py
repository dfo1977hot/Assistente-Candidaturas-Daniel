"""Migration history and feature flags entities."""

from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, JSON, Text

from acd.models.base import Base


class MigrationStatus(str, Enum):
    """Migration status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


class MigrationHistory(Base):
    """Database and data migrations history."""

    __tablename__ = "migration_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    migration_name: Mapped[str] = mapped_column(unique=True, index=True)  # v0.3.0_to_v0.4.0_users
    source_version: Mapped[str] = mapped_column(index=True)
    target_version: Mapped[str] = mapped_column(index=True)
    migration_type: Mapped[str]  # DATABASE, CONFIGURATION, FILES, DATA_MAPPING
    migration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
    )
    completion_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str]  # PENDING, IN_PROGRESS, COMPLETED, FAILED, VERIFIED
    duration_seconds: Mapped[int] = mapped_column(default=0)
    records_migrated: Mapped[int] = mapped_column(default=0)
    records_failed: Mapped[int] = mapped_column(default=0)
    rollback_available: Mapped[bool] = mapped_column(default=True)
    migration_details: Mapped[dict] = mapped_column(JSON, default={})
    error_message: Mapped[str | None] = mapped_column(nullable=True)
    validation_results: Mapped[dict] = mapped_column(JSON, default={})
    migration_script: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )

    def is_successful(self) -> bool:
        """Check if migration was successful."""
        return self.status == MigrationStatus.COMPLETED.value

    def is_failed(self) -> bool:
        """Check if migration failed."""
        return self.status == MigrationStatus.FAILED.value

    def is_verified(self) -> bool:
        """Check if migration was verified."""
        return self.status == MigrationStatus.VERIFIED.value

    def success_rate(self) -> float:
        """Calculate migration success rate."""
        total = self.records_migrated + self.records_failed
        if total == 0:
            return 100.0
        return (self.records_migrated / total) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "migration_name": self.migration_name,
            "source_version": self.source_version,
            "target_version": self.target_version,
            "status": self.status,
            "migration_date": self.migration_date.isoformat(),
            "duration_seconds": self.duration_seconds,
            "records_migrated": self.records_migrated,
            "success_rate": self.success_rate(),
        }


class FeatureFlag(Base):
    """Feature flags for feature toggling."""

    __tablename__ = "feature_flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    feature_name: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str] = mapped_column(default="")
    is_enabled: Mapped[bool] = mapped_column(default=False, index=True)
    is_beta: Mapped[bool] = mapped_column(default=False)
    rollout_percentage: Mapped[int] = mapped_column(default=0)  # 0-100
    target_versions: Mapped[list[str]] = mapped_column(JSON, default=[])  # Empty = all
    experimental: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
    )

    def is_enabled_for_version(self, version: str) -> bool:
        """Check if feature is enabled for a specific version."""
        if not self.is_enabled:
            return False
        if self.target_versions and version not in self.target_versions:
            return False
        return True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "feature_name": self.feature_name,
            "description": self.description,
            "is_enabled": self.is_enabled,
            "is_beta": self.is_beta,
            "rollout_percentage": self.rollout_percentage,
            "experimental": self.experimental,
        }
