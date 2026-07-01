from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class Task(Base):
    """Individual task within an execution plan."""

    __tablename__ = "agent_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("execution_plans.id"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)  # analyze, generate, execute, etc
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)  # ATS, Career, Workflow, etc
    parameters: Mapped[str] = mapped_column(Text, nullable=True)  # JSON serialized
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, running, completed, failed
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    dependencies: Mapped[str] = mapped_column(Text, nullable=True)  # JSON serialized task IDs
    estimated_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    actual_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result: Mapped[str] = mapped_column(Text, nullable=True)  # JSON serialized result
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
