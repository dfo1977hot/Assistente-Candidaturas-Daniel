from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class AgentGoal(Base):
    """Objective for the AI agent to accomplish."""

    __tablename__ = "agent_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    objective_type: Mapped[str] = mapped_column(String(50), nullable=False)  # job_search, career_planning, etc
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, planning, executing, completed, failed
    success_rate: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=0, nullable=False)
    decomposed: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
