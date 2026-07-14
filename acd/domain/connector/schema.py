from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class PlatformSchema(Base):
    """Esquema de campos de uma plataforma."""

    __tablename__ = "platform_schemas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1")
    fields: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
