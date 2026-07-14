from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class SocialLink(Base):
    """Social network or professional link associated with a profile."""

    __tablename__ = "social_links"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
    )

    url: Mapped[str] = mapped_column(
        String(300),
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
            f"SocialLink("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"url={self.url!r})"
        )