from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class AgentMemory(Base):
    """Agent memory storing conversations, decisions, and preferences."""

    __tablename__ = "agent_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)  # conversation, decision, preference, summary
    key: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON serialized
    context: Mapped[str] = mapped_column(Text, nullable=True)  # Related context
    importance: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-10
    expiration_days: Mapped[int] = mapped_column(Integer, nullable=True)  # None = persistent
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
