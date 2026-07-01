from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class ConnectorSetting(Base):
    """Configurações persistidas de um conector."""

    __tablename__ = "connector_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    connector_name: Mapped[str] = mapped_column(String(100), nullable=False)
    setting_name: Mapped[str] = mapped_column(String(100), nullable=False)
    setting_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
