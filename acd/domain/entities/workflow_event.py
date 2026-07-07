from __future__ import annotations
from acd.core.datetime_utils import utc_now

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class WorkflowEvent(Base):
    """Event Store: tracks all events from workflow execution."""

    __tablename__ = "workflow_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_execution_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_executions.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_data: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
