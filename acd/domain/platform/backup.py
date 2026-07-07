"""Backup entity for data preservation."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class BackupType(StrEnum):
    """Types of backups."""

    MANUAL = "manual"
    AUTOMATIC = "automatic"
    FULL = "full"
    INCREMENTAL = "incremental"


class BackupStatus(StrEnum):
    """Backup status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RESTORED = "restored"


class Backup(Base):
    """Backup record for disaster recovery."""

    __tablename__ = "system_backups"

    id: Mapped[int] = mapped_column(primary_key=True)
    backup_type: Mapped[str]  # MANUAL, AUTOMATIC, FULL, INCREMENTAL
    status: Mapped[str]  # PENDING, IN_PROGRESS, COMPLETED, FAILED, RESTORED
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str] = mapped_column(default="")
    file_path: Mapped[str]
    file_size_mb: Mapped[float] = mapped_column(default=0.0)
    database_records: Mapped[int] = mapped_column(default=0)
    files_included: Mapped[int] = mapped_column(default=0)
    config_included: Mapped[bool] = mapped_column(default=True)
    logs_included: Mapped[bool] = mapped_column(default=False)
    checksum: Mapped[str | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(nullable=True)
    backup_metadata: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    restored_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def is_complete(self) -> bool:
        """Check if backup is complete."""
        return self.status == BackupStatus.COMPLETED.value

    def is_failed(self) -> bool:
        """Check if backup failed."""
        return self.status == BackupStatus.FAILED.value

    def is_restorable(self) -> bool:
        """Check if backup can be restored."""
        return self.status == BackupStatus.COMPLETED.value

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "backup_type": self.backup_type,
            "status": self.status,
            "name": self.name,
            "description": self.description,
            "file_size_mb": self.file_size_mb,
            "database_records": self.database_records,
            "files_included": self.files_included,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
