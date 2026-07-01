from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class AutomationSession(Base):
    """Sessão de automação vinculada a uma candidatura."""

    __tablename__ = "automation_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"), nullable=True)
    platform: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    browser: Mapped[str] = mapped_column(String(100), nullable=False, default="chromium")
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="headless")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="started")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    execution_time: Mapped[float] = mapped_column(Integer, nullable=False, default=0)
    screenshot_path: Mapped[str] = mapped_column(Text, nullable=False, default="")
    error_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
