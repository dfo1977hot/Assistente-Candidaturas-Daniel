from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class PipelineExecution(Base):
    """Persisted history record for one Intelligent Application Pipeline run."""

    __tablename__ = "pipeline_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    pipeline_id: Mapped[str] = mapped_column(String(100), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stages: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    failures: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    warnings: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    diagnostics: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
