"""Agent session entity."""

from datetime import datetime
from typing import Any

from sqlalchemy import String, Text, Integer, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class AgentSession(Base):
    """Agent session entity for tracking conversations."""

    __tablename__ = "agent_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    session_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Tracking
    is_active: Mapped[bool] = mapped_column(default=True)
    task_count: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Context
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    session_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<AgentSession(id={self.id}, title={self.title}, is_active={self.is_active})>"
