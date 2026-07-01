"""Release entity for version management."""

from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, DateTime, Text

from acd.models.base import Base


class ReleaseStatus(str, Enum):
    """Release status enumeration."""

    DRAFT = "draft"
    BETA = "beta"
    STABLE = "stable"
    EOL = "eol"  # End of Life


class Release(Base):
    """Release record for version management."""

    __tablename__ = "system_releases"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(unique=True, index=True)  # SemVer: 0.4.0
    release_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
    )
    status: Mapped[str]  # DRAFT, BETA, STABLE, EOL
    release_notes: Mapped[str] = mapped_column(Text, default="")
    changelog: Mapped[dict] = mapped_column(JSON, default={})  # {feature_name: description}
    download_url: Mapped[str | None] = mapped_column(nullable=True)
    file_size_mb: Mapped[float] = mapped_column(default=0.0)
    file_hash: Mapped[str | None] = mapped_column(nullable=True)  # SHA-256
    min_previous_version: Mapped[str | None] = mapped_column(nullable=True)  # For migration path
    breaking_changes: Mapped[list[str]] = mapped_column(JSON, default=[])
    new_features: Mapped[list[str]] = mapped_column(JSON, default=[])
    bug_fixes: Mapped[list[str]] = mapped_column(JSON, default=[])
    dependencies: Mapped[dict] = mapped_column(JSON, default={})  # {dep_name: version}
    is_critical: Mapped[bool] = mapped_column(default=False)  # Critical security update
    requires_backup: Mapped[bool] = mapped_column(default=True)
    installation_guide: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
    )

    def is_stable(self) -> bool:
        """Check if release is stable."""
        return self.status == ReleaseStatus.STABLE.value

    def is_beta(self) -> bool:
        """Check if release is beta."""
        return self.status == ReleaseStatus.BETA.value

    def is_eol(self) -> bool:
        """Check if release is end of life."""
        return self.status == ReleaseStatus.EOL.value

    def get_summary(self) -> str:
        """Get human-readable summary."""
        return f"Release {self.version} ({self.status}) - {self.release_date.strftime('%Y-%m-%d')}"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "version": self.version,
            "status": self.status,
            "release_date": self.release_date.isoformat(),
            "release_notes": self.release_notes,
            "new_features": self.new_features,
            "bug_fixes": self.bug_fixes,
            "breaking_changes": self.breaking_changes,
            "is_critical": self.is_critical,
        }
