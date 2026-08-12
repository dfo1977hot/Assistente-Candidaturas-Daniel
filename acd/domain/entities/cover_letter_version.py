from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class CoverLetterVersion(Base):
    """Carta de apresentação versionada e vinculada ao contexto da candidatura."""

    __tablename__ = "cover_letter_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    curriculum_id: Mapped[int] = mapped_column(
        ForeignKey("curricula.id"),
        nullable=False,
    )
    job_id: Mapped[int | None] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=True,
        index=True,
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id"),
        nullable=True,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    letter_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="Carta de Apresentação",
    )
    language: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Português",
    )
    tone: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="Profissional",
    )
    length: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Média",
    )
    subject: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Rascunho",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
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
