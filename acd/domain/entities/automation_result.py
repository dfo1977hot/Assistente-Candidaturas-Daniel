from __future__ import annotations
from acd.core.datetime_utils import utc_now

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class AutomationResult(Base):
    """Resultado final de uma execução de automação."""

    __tablename__ = "automation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"), nullable=True)
    connector: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    execution_time: Mapped[float] = mapped_column(Integer, nullable=False, default=0)
    screenshot: Mapped[str] = mapped_column(Text, nullable=False, default="")
    error_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
