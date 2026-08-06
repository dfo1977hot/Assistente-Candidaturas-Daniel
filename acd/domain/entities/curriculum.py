from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acd.core.datetime_utils import utc_now
from acd.models.base import Base

if TYPE_CHECKING:
    from acd.domain.entities.curriculum_version import CurriculumVersion


class Curriculum(Base):
    __tablename__ = "curricula"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    structured_content_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0")
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="pt-BR")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Ativo")

    file_original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_relative_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_extension: Mapped[str | None] = mapped_column(String(10), nullable=True)
    file_mime_type: Mapped[str | None] = mapped_column(String(150), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_attached_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    versions: Mapped[list[CurriculumVersion]] = relationship(
        "CurriculumVersion",
        back_populates="curriculum",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Curriculum(id={self.id!r}, name={self.name!r}, version={self.version!r})"
