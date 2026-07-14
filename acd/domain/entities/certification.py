from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class Certification(Base):
    """Catalog of professional certifications."""

    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
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

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""

        return (
            f"Certification("
            f"id={self.id!r}, "
            f"name={self.name!r})"
        )