"""Outcome entity for recording results of actions."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from acd.core.datetime_utils import utc_now

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class OutcomeType(StrEnum):
    """Type of outcome."""

    APPLICATION_SUBMITTED = "application_submitted"
    INTERVIEW_RECEIVED = "interview_received"
    REJECTION = "rejection"
    INTERVIEW_PASSED = "interview_passed"
    JOB_OFFER = "job_offer"
    APPLICATION_VIEWED = "application_viewed"
    LETTER_RESPONSE = "letter_response"
    PROFILE_VIEWED = "profile_viewed"


class OutcomeResult(StrEnum):
    """Result of outcome."""

    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class Outcome(Base):
    """Record of a result from an action or application."""

    __tablename__ = "outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    outcome_type: Mapped[str] = mapped_column(SQLEnum(OutcomeType), nullable=False, index=True)
    result: Mapped[str] = mapped_column(SQLEnum(OutcomeResult), nullable=False, index=True)
    application_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True, comment="Related application ID"
    )
    curriculum_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="Resume used")
    letter_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="Letter used")
    company: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(100), nullable=True, comment="Platform used")
    position_title: Mapped[str] = mapped_column(String(300), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=True, comment="Industry sector")
    skills_mentioned: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="Additional context"
    )
    time_to_outcome: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Days until outcome (if applicable)"
    )
    quality_feedback: Mapped[str] = mapped_column(
        Text, default="", nullable=False, comment="User feedback on quality"
    )
    relevance_score: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False, default=0.5
    )
    engagement_level: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False, comment="High/Medium/Low"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False, index=True
    )
    recorded_date: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False, comment="When outcome occurred"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Outcome id={self.id} type={self.outcome_type} result={self.result}>"

    def is_positive(self) -> bool:
        """Check if outcome is positive (success)."""
        return self.result == OutcomeResult.SUCCESS

    def is_negative(self) -> bool:
        """Check if outcome is negative (failure)."""
        return self.result == OutcomeResult.FAILURE

    def get_context_item(self, key: str, default: Any = None) -> Any:
        """Get context item by key."""
        if not isinstance(self.context, dict):
            self.context = {}
        return self.context.get(key, default)

    def add_context(self, key: str, value: Any) -> None:
        """Add context information.

        Args:
            key: Context key
            value: Context value
        """
        if not isinstance(self.context, dict):
            self.context = {}
        self.context[key] = value
