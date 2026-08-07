"""Update history and installation logs entities."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class UpdateStatus(StrEnum):
    """Update status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class UpdateHistory(Base):
    """Track system updates."""

    __tablename__ = "update_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_version: Mapped[str] = mapped_column(index=True)
    to_version: Mapped[str] = mapped_column(index=True)
    update_type: Mapped[str]  # MINOR, MAJOR, PATCH, BETA
    update_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
    )
    completion_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str]  # PENDING, IN_PROGRESS, COMPLETED, FAILED, ROLLED_BACK
    duration_minutes: Mapped[int] = mapped_column(default=0)
    download_size_mb: Mapped[float] = mapped_column(default=0.0)
    install_size_mb: Mapped[float] = mapped_column(default=0.0)
    is_automatic: Mapped[bool] = mapped_column(default=False)
    rollback_available: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str | None] = mapped_column(nullable=True)
    error_type: Mapped[str | None] = mapped_column(nullable=True)
    update_metadata: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )

    def is_successful(self) -> bool:
        """Check if update was successful."""
        return self.status == UpdateStatus.COMPLETED.value

    def is_failed(self) -> bool:
        """Check if update failed."""
        return self.status == UpdateStatus.FAILED.value

    def can_rollback(self) -> bool:
        """Check if rollback is available."""
        return self.rollback_available and self.status == UpdateStatus.COMPLETED.value

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "status": self.status,
            "update_date": self.update_date.isoformat(),
            "duration_minutes": self.duration_minutes,
            "is_automatic": self.is_automatic,
            "can_rollback": self.can_rollback(),
        }


class InstallationLog(Base):
    """Installation operations log."""

    __tablename__ = "installation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    operation: Mapped[str] = mapped_column(index=True)  # INSTALL, UPDATE, MIGRATE, ROLLBACK
    status: Mapped[str]  # SUCCESS, FAILED, IN_PROGRESS, ABORTED
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_seconds: Mapped[int] = mapped_column(default=0)
    message: Mapped[str]
    details: Mapped[dict] = mapped_column(JSON, default={})
    error_message: Mapped[str | None] = mapped_column(nullable=True)
    error_stack: Mapped[str | None] = mapped_column(nullable=True)
    installation_logs: Mapped[list[str]] = mapped_column(JSON, default=[])
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )

    def is_successful(self) -> bool:
        """Check if operation was successful."""
        return self.status == "SUCCESS"

    def is_failed(self) -> bool:
        """Check if operation failed."""
        return self.status == "FAILED"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "operation": self.operation,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "message": self.message,
        }
