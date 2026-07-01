from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class BrowserProfile(Base):
    """Perfil do navegador para execução de automações."""

    __tablename__ = "browser_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    browser: Mapped[str] = mapped_column(String(100), nullable=False, default="chromium")
    headless: Mapped[bool] = mapped_column(Integer, nullable=False, default=1)
