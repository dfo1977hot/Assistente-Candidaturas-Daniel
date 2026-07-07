from __future__ import annotations
from acd.core.datetime_utils import utc_now

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acd.models.base import Base


class Curriculum(Base):
    """Entidade de domínio para currículos."""

    __tablename__ = "curricula"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0")
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="pt-BR")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Ativo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    versions: Mapped[list[CurriculumVersion]] = relationship(back_populates="curriculum")

    def __repr__(self) -> str:
        return f"<Curriculum {self.name} {self.version}>"
