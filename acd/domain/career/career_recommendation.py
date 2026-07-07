from __future__ import annotations
from acd.core.datetime_utils import utc_now

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class CareerRecommendation(Base):
    """Career development recommendation with impact and effort metrics."""

    __tablename__ = "career_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("career_goals.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="skills")
    impact: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False, default=5)
    effort: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False, default=5)
    priority_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=0)
    estimated_duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    dependencies: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
