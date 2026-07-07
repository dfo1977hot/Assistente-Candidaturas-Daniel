"""Pattern entity for detected patterns in data."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class PatternType(StrEnum):
    """Type of pattern detected."""

    CONVERSION_RATE = "conversion_rate"
    RESPONSE_TIME = "response_time"
    SKILL_SUCCESS = "skill_success"
    PLATFORM_SUCCESS = "platform_success"
    RESUME_TYPE_SUCCESS = "resume_type_success"
    TIMING_PATTERN = "timing_pattern"
    SECTOR_PATTERN = "sector_pattern"
    LETTER_EFFECTIVENESS = "letter_effectiveness"
    CUSTOM = "custom"


class Pattern(Base):
    """Detected pattern in application data."""

    __tablename__ = "patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    pattern_type: Mapped[str] = mapped_column(SQLEnum(PatternType), nullable=False, index=True)
    criteria: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    criteria_explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False, default=0.5
    )
    frequency: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="How often pattern occurs"
    )
    impact_score: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False, default=0.0, comment="Expected impact (0-1)"
    )
    related_learning_records: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC), nullable=False)
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Pattern id={self.id} name={self.name} type={self.pattern_type} evidence={self.evidence_count}>"

    def add_evidence(self, evidence_count: int = 1, impact_delta: float = 0.0) -> None:
        """Add evidence to the pattern.

        Args:
            evidence_count: Number of evidence items to add
            impact_delta: Change in impact score
        """
        self.evidence_count += evidence_count
        self.frequency += 1
        self.impact_score = min(1.0, float(self.impact_score) + impact_delta)
        self.updated_at = datetime.now(UTC)

    def confirm(self) -> None:
        """Mark pattern as confirmed."""
        self.last_confirmed_at = datetime.now(UTC)

    def get_confidence_percentage(self) -> float:
        """Get confidence as percentage."""
        return float(self.confidence) * 100

    def get_impact_percentage(self) -> float:
        """Get impact as percentage."""
        return float(self.impact_score) * 100
