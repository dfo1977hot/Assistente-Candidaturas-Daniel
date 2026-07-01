"""Agent task entity."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import String, Text, Integer, DateTime, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class TaskStatus(str, Enum):
    """Task status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentTask(Base):
    """Agent task entity."""

    __tablename__ = "agent_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("agent_sessions.id"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    
    status: Mapped[str] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority: Mapped[str] = mapped_column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Task definition
    task_type: Mapped[str] = mapped_column(String(50))
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    expected_output: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Execution
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Tracking
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    actual_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Dependencies
    depends_on: Mapped[list[int]] = mapped_column(JSON, default=list)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<AgentTask(id={self.id}, agent_id={self.agent_id}, status={self.status})>"
