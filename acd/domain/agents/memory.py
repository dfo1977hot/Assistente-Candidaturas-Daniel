"""Agent memory entity."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import String, Text, Integer, DateTime, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class MemoryType(str, Enum):
    """Memory type."""

    TEMPORARY = "temporary"  # Valid during session
    PERSISTENT = "persistent"  # Preserved across sessions
    DECISION = "decision"  # Decision records
    PREFERENCE = "preference"  # User preferences
    HISTORY = "history"  # Historical records


class AgentMemory(Base):
    """Agent memory entity."""

    __tablename__ = "agent_memory"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("agent_sessions.id"), nullable=True)
    
    memory_type: Mapped[str] = mapped_column(SQLEnum(MemoryType), index=True)
    key: Mapped[str] = mapped_column(String(200), index=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON)
    
    # Context
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    importance: Mapped[int] = mapped_column(Integer, default=1)  # 1-10
    
    # TTL for temporary memories
    expiration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    accessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<AgentMemory(id={self.id}, agent_id={self.agent_id}, key={self.key})>"
