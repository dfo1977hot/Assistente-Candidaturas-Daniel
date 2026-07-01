from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acd.models.base import Base
from acd.models.company import Company
from acd.domain.entities.job import Job


class Application(Base):
    """Entidade de domínio para uma candidatura."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    curriculum_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    curriculum_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="")
    cover_letter_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Rascunho")
    application_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_update: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_follow_up: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    response_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    interview_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    salary_expected: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    salary_offered: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    application_channel: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    recruiter_name: Mapped[str] = mapped_column(String(200), nullable=True, default="")
    recruiter_email: Mapped[str] = mapped_column(String(200), nullable=True, default="")
    recruiter_phone: Mapped[str] = mapped_column(String(50), nullable=True, default="")
    feedback: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    notes: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    job: Mapped[Job] = relationship("Job")
    company: Mapped[Company] = relationship("Company")

    def __repr__(self) -> str:
        return f"<Application {self.id}>"
