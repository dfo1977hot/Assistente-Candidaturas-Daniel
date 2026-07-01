"""Agent tool entity."""

from datetime import datetime
from typing import Any

from sqlalchemy import String, Text, Integer, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class AgentTool(Base):
    """Agent authorized tool entity."""

    __tablename__ = "agent_tools"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    
    tool_name: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    
    # Access control
    is_authorized: Mapped[bool] = mapped_column(default=True)
    requires_approval: Mapped[bool] = mapped_column(default=False)
    
    # Usage tracking
    max_calls_per_session: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_calls_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calls_made: Mapped[int] = mapped_column(Integer, default=0)
    
    # Configuration
    input_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AgentTool(id={self.id}, agent_id={self.agent_id}, tool_name={self.tool_name})>"
