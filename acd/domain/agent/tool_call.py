from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class ToolCall(Base):
    """Records tool invocations by the agent."""

    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("execution_plans.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("agent_tasks.id"), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_version: Mapped[str] = mapped_column(String(50), nullable=True)
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[str] = mapped_column(Text, nullable=False)  # JSON serialized
    result: Mapped[str] = mapped_column(Text, nullable=True)  # JSON serialized
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, running, success, failed
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    duration_milliseconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
