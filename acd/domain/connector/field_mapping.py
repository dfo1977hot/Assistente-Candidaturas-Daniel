from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class FieldMapping(Base):
    """Mapeamento entre um campo do perfil e um campo da plataforma."""

    __tablename__ = "field_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), nullable=False)
    source_field: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    target_field: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    transformation: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mapping_metadata: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
