from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal

from acd.models.base import Base


class CareerSkillGap(Base):
    """Analysis of skill gaps between current profile and career goal."""

    __tablename__ = "career_skill_gaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("career_goals.id"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(200), nullable=False)
    current_level: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False, default=0)
    required_level: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False, default=5)
    gap_severity: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    gap_type: Mapped[str] = mapped_column(String(50), nullable=False, default="skill")
    learning_path: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estimated_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
