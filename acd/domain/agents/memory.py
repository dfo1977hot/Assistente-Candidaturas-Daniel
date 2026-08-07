"""Agent memory entity."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class MemoryType(StrEnum):
    """Tipos de memória compatíveis com o sistema legado e Multi-Agent."""

    # -------- Legado --------
    CONVERSATION = "conversation"
    DECISION = "decision"
    PREFERENCE = "preference"
    SUMMARY = "summary"

    # -------- Multi-Agent --------
    TEMPORARY = "temporary"
    PERSISTENT = "persistent"
    HISTORY = "history"


class AgentMemory(Base):
    """Agent memory entity.

    Este modelo é compatível tanto com o sistema Multi-Agent quanto com o
    sistema legado de IA durante o período de migração.
    """

    __tablename__ = "agent_memory"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Multi-Agent
    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id"),
        nullable=True,
        index=True,
    )

    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("agent_sessions.id"),
        nullable=True,
    )

    # Dados da memória
    memory_type: Mapped[MemoryType] = mapped_column(
        SQLEnum(
            MemoryType,
            values_callable=lambda enum: [e.value for e in enum],
        ),
        index=True,
    )

    key: Mapped[str] = mapped_column(
        String(200),
        index=True,
    )

    value: Mapped[dict[str, Any]] = mapped_column(JSON)

    # Contexto
    context: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )

    importance: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    # TTL
    expiration_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Compatibilidade com o modelo legado
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AgentMemory("
            f"id={self.id}, "
            f"agent_id={self.agent_id}, "
            f"key={self.key})>"
        )