from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class ReasoningStep(Base):
    """Records reasoning steps taken by the agent."""

    __tablename__ = "reasoning_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("agent_goals.id"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # decompose, analyze, decide, plan, etc
    input_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON serialized
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)  # Explanation
    conclusion: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_level: Mapped[float] = mapped_column(default=0.5, nullable=False)  # 0.0-1.0
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
