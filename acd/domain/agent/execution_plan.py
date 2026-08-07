from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class ExecutionPlan(Base):
    """Executable plan created by the agent."""

    __tablename__ = "execution_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("agent_goals.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    strategy: Mapped[str] = mapped_column(Text, nullable=False)  # Explanation of chosen strategy
    tasks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, approved, executing, completed, failed, cancelled
    approval_status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, approved, rejected
    requires_human_approval: Mapped[bool] = mapped_column(default=False, nullable=False)
    estimated_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    actual_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_summary: Mapped[str] = mapped_column(Text, nullable=True)  # JSON serialized
    approved_by_user: Mapped[bool] = mapped_column(default=False, nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
