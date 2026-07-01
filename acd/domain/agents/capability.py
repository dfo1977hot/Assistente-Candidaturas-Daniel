"""Agent capability entity."""

from datetime import datetime
from typing import Any

from sqlalchemy import String, Text, Integer, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class AgentCapability(Base):
    """Agent capability/permission entity."""

    __tablename__ = "agent_capabilities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text)
    capability_type: Mapped[str] = mapped_column(String(50))  # tool, action, analysis, etc
    
    # Configuration
    is_enabled: Mapped[bool] = mapped_column(default=True)
    requires_approval: Mapped[bool] = mapped_column(default=False)
    
    # Limitations
    max_invocations_per_session: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Metadata
    version: Mapped[int] = mapped_column(Integer, default=1)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AgentCapability(id={self.id}, agent_id={self.agent_id}, name={self.name})>"
