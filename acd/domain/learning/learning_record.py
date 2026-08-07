"""Learning record entity for storing observed outcomes and learned insights."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class LearningRecordStatus(StrEnum):
    """Learning record status."""

    DETECTED = "detected"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class LearningSourceType(StrEnum):
    """Source of learning data."""

    ATS_ENGINE = "ats_engine"
    ANALYTICS = "analytics"
    WORKFLOW_ENGINE = "workflow_engine"
    AUTOMATION_ENGINE = "automation_engine"
    CAREER_AI = "career_ai"
    CRM = "crm"
    USER_FEEDBACK = "user_feedback"
    PATTERN_DETECTION = "pattern_detection"


class LearningRecord(Base):
    """Record of a learning event or insight detected by the system."""

    __tablename__ = "learning_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(
        SQLEnum(LearningSourceType), nullable=False, default=LearningSourceType.PATTERN_DETECTION
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    confidence: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False, default=0.5
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(LearningRecordStatus),
        nullable=False,
        default=LearningRecordStatus.DETECTED,
        index=True,
    )
    approver_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<LearningRecord id={self.id} source={self.source} status={self.status} confidence={self.confidence}>"

    def approve(self, notes: str = "") -> None:
        """Mark learning record as approved.

        Args:
            notes: Optional approval notes
        """
        self.status = LearningRecordStatus.APPROVED
        self.approved_at = datetime.now(UTC)
        self.approver_notes = notes

    def reject(self, notes: str = "") -> None:
        """Mark learning record as rejected.

        Args:
            notes: Optional rejection notes
        """
        self.status = LearningRecordStatus.REJECTED
        self.rejected_at = datetime.now(UTC)
        self.approver_notes = notes

    def is_approved(self) -> bool:
        """Check if record is approved."""
        return self.status == LearningRecordStatus.APPROVED

    def get_confidence_percentage(self) -> float:
        """Get confidence as percentage."""
        return float(self.confidence) * 100
