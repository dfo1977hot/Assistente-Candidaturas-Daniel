from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acd.core.datetime_utils import utc_now
from acd.models.base import Base

if TYPE_CHECKING:
    from acd.domain.entities.curriculum_version import (
        CurriculumVersion,
    )


class Curriculum(Base):
    """Domain entity representing a curriculum."""

    __tablename__ = "curricula"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        default="",
    )

    structured_content_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="v1.0",
    )

    language: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pt-BR",
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Ativo",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    versions: Mapped[list[CurriculumVersion]] = relationship(
        "CurriculumVersion",
        back_populates="curriculum",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""

        return (
            f"Curriculum("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"version={self.version!r})"
        )
