"""Agent message entity."""

from __future__ import annotations
from acd.core.datetime_utils import utc_now

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class MessageType(StrEnum):
    """Message types in multi-agent communication."""

    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    REQUEST_INFORMATION = "request_information"
    NEED_APPROVAL = "need_approval"
    EXECUTION_FINISHED = "execution_finished"
    STATUS_UPDATE = "status_update"
    ERROR = "error"


class AgentMessage(Base):
    """Agent message entity for Message Bus communication."""

    __tablename__ = "agent_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("agent_sessions.id"),
        nullable=True,
    )

    # Message metadata
    message_type: Mapped[str] = mapped_column(
        SQLEnum(MessageType),
        index=True,
    )

    sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id"),
        nullable=True,
    )

    receiver_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id"),
        nullable=True,
    )

    # Message content
    subject: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Tracking
    is_read: Mapped[bool] = mapped_column(default=False)
    response_required: Mapped[bool] = mapped_column(default=False)
    response_deadline: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Relationships
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("multi_agent_tasks.id"),
        nullable=True,
    )

    parent_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("agent_messages.id"),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AgentMessage("
            f"id={self.id}, "
            f"type={self.message_type}, "
            f"sender_id={self.sender_id})>"
        )