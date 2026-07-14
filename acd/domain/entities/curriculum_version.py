from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acd.core.datetime_utils import utc_now
from acd.models.base import Base

if TYPE_CHECKING:
    from acd.domain.entities.curriculum import Curriculum


class CurriculumVersion(Base):
    """Represents a persisted version of a curriculum."""

    __tablename__ = "curriculum_versions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    curriculum_id: Mapped[int] = mapped_column(
        ForeignKey("curricula.id"),
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        default="",
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )

    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
    )

    checksum: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    curriculum: Mapped[Curriculum] = relationship(
        "Curriculum",
        back_populates="versions",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""

        return (
            f"CurriculumVersion("
            f"id={self.id!r}, "
            f"version={self.version!r})"
        )