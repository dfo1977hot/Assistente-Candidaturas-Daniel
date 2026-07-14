from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class JobProfile(Base):
    """Perfil estruturado de uma vaga."""

    __tablename__ = "job_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    structured_description: Mapped[str] = mapped_column(Text, nullable=True, default="")
    seniority: Mapped[str] = mapped_column(String(50), nullable=True, default="")
    work_model: Mapped[str] = mapped_column(String(50), nullable=True, default="")
    language: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    skills: Mapped[str] = mapped_column(Text, nullable=True, default="")
    technologies: Mapped[str] = mapped_column(Text, nullable=True, default="")
    methodologies: Mapped[str] = mapped_column(Text, nullable=True, default="")
    languages: Mapped[str] = mapped_column(Text, nullable=True, default="")
    certifications: Mapped[str] = mapped_column(Text, nullable=True, default="")
    keywords: Mapped[str] = mapped_column(Text, nullable=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
