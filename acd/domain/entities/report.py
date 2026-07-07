from __future__ import annotations
from acd.core.datetime_utils import utc_now

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class Report(Base):
    """Generated analytics report."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    period: Mapped[str] = mapped_column(String(50), nullable=False, default="daily")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="pdf")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
