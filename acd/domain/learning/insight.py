"""Insight entity for actionable knowledge derived from patterns."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import String, Text, Integer, DateTime, JSON, Enum as SQLEnum, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class InsightType(str, Enum):
    """Type of insight."""

    CONVERSION_TIP = "conversion_tip"
    SKILL_RECOMMENDATION = "skill_recommendation"
    PLATFORM_ADVICE = "platform_advice"
    TIMING_INSIGHT = "timing_insight"
    LETTER_IMPROVEMENT = "letter_improvement"
    SECTOR_STRATEGY = "sector_strategy"
    RESUME_OPTIMIZATION = "resume_optimization"
    GENERAL_RECOMMENDATION = "general_recommendation"


class Insight(Base):
    """Actionable knowledge derived from patterns."""

    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    insight_type: Mapped[str] = mapped_column(SQLEnum(InsightType), nullable=False, index=True)
    expected_impact: Mapped[str] = mapped_column(Text, nullable=False, comment="Expected impact if applied")
    confidence: Mapped[float] = mapped_column(Numeric(precision=5, scale=4), nullable=False, default=0.5)
    origin: Mapped[str] = mapped_column(String(200), nullable=False, comment="Where insight came from")
    related_patterns: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    related_hypotheses: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    recommendations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    evidence_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    analysis_period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    analysis_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_points_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    user_feedback: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Insight id={self.id} title={self.title} type={self.insight_type}>"

    def mark_applied(self) -> None:
        """Mark insight as applied."""
        self.is_applied = True
        self.applied_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_recommendation(self, recommendation: dict[str, Any]) -> None:
        """Add recommendation to insight.

        Args:
            recommendation: Recommendation object with action, rationale, expected_benefit
        """
        if not isinstance(self.recommendations, list):
            self.recommendations = []
        self.recommendations.append(recommendation)
        self.updated_at = datetime.utcnow()

    def get_confidence_percentage(self) -> float:
        """Get confidence as percentage."""
        return float(self.confidence) * 100

    def get_summary(self) -> dict[str, Any]:
        """Get insight summary for presentation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.insight_type,
            "confidence": self.get_confidence_percentage(),
            "expected_impact": self.expected_impact,
            "recommendations": self.recommendations,
            "origin": self.origin,
            "is_actionable": self.is_actionable,
            "is_applied": self.is_applied,
        }
