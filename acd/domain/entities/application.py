from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acd.core.datetime_utils import utc_now
from acd.domain.entities.job import Job
from acd.models.base import Base
from acd.models.company import Company


class Application(Base):
    """Entidade de domínio para uma candidatura."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    curriculum_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selected_resume_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("resume_versions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        default=None,
    )
    curriculum_version: Mapped[str | None] = mapped_column(String(50), nullable=True, default="")
    cover_letter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Rascunho")
    application_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_update: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_follow_up: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_action: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    follow_up_time: Mapped[str] = mapped_column(String(5), nullable=False, default="")
    follow_up_priority: Mapped[str] = mapped_column(String(20), nullable=False, default="Normal")
    follow_up_note: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    response_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interview_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    salary_expected: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    salary_offered: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    application_channel: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    recruiter_name: Mapped[str] = mapped_column(String(200), nullable=True, default="")
    recruiter_email: Mapped[str] = mapped_column(String(200), nullable=True, default="")
    recruiter_phone: Mapped[str] = mapped_column(String(50), nullable=True, default="")
    feedback: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    notes: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    job: Mapped[Job] = relationship("Job")
    company: Mapped[Company] = relationship("Company")

    def __repr__(self) -> str:
        return f"<Application {self.id}>"
