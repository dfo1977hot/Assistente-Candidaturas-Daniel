from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class Profile(Base):
    """Unified professional profile of the user."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="",
    )

    preferred_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="",
    )

    email: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="",
    )

    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
    )

    linkedin_url: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        default="",
    )

    github_url: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        default="",
    )

    portfolio_url: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        default="",
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    location: Mapped[str] = mapped_column(
        String(200),
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
            f"Profile("
            f"id={self.id!r}, "
            f"full_name={self.full_name!r}, "
            f"email={self.email!r})"
        )