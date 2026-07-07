"""Hypothesis entity for testable assumptions about patterns."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class HypothesisStatus(StrEnum):
    """Hypothesis status."""

    PROPOSED = "proposed"
    TESTING = "testing"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    PENDING_REVIEW = "pending_review"
    REJECTED_BY_USER = "rejected_by_user"


class Hypothesis(Base):
    """Testable hypothesis about data patterns."""

    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    statement: Mapped[str] = mapped_column(String(500), nullable=False, unique=False, index=True)
    confidence: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False, default=0.5
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(HypothesisStatus), nullable=False, default=HypothesisStatus.PROPOSED, index=True
    )
    evidence_base: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="Evidence supporting hypothesis"
    )
    evidence_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of data points"
    )
    counterevidence: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="Counter evidence"
    )
    counterevidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    test_period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    test_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expected_impact: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="Expected impact if true"
    )
    related_patterns: Mapped[list[int]] = mapped_column(
        JSON, default=list, nullable=False, comment="Related pattern IDs"
    )
    related_learning_records: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    user_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Hypothesis id={self.id} status={self.status} confidence={self.confidence}>"

    def confirm(self, notes: str = "") -> None:
        """Mark hypothesis as confirmed.

        Args:
            notes: Optional notes
        """
        self.status = HypothesisStatus.CONFIRMED
        self.reviewed_at = datetime.now(UTC)
        if notes:
            self.user_notes = notes

    def refute(self, notes: str = "") -> None:
        """Mark hypothesis as refuted.

        Args:
            notes: Optional notes
        """
        self.status = HypothesisStatus.REFUTED
        self.reviewed_at = datetime.now(UTC)
        if notes:
            self.user_notes = notes

    def reject(self, notes: str = "") -> None:
        """Mark hypothesis as rejected by user.

        Args:
            notes: Optional notes
        """
        self.status = HypothesisStatus.REJECTED_BY_USER
        self.reviewed_at = datetime.now(UTC)
        if notes:
            self.user_notes = notes

    def add_evidence(self, evidence_item: dict[str, Any]) -> None:
        """Add supporting evidence to hypothesis.

        Args:
            evidence_item: Evidence data
        """
        if not isinstance(self.evidence_base, dict):
            self.evidence_base = {}
        self.evidence_base[str(len(self.evidence_base))] = evidence_item
        self.evidence_count += 1
        self.updated_at = datetime.now(UTC)

    def get_confidence_percentage(self) -> float:
        """Get confidence as percentage."""
        return float(self.confidence) * 100

    def is_pending_review(self) -> bool:
        """Check if hypothesis is pending review."""
        return self.status == HypothesisStatus.PENDING_REVIEW
