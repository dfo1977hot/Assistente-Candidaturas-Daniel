from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class Education(Base):
    """Educational background of the user."""

    __tablename__ = "educations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id"),
        nullable=False,
    )

    institution: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="",
    )

    degree: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="",
    )

    field: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="",
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
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
            f"Education("
            f"id={self.id!r}, "
            f"institution={self.institution!r}, "
            f"degree={self.degree!r})"
        )