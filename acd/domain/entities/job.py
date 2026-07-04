from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acd.models.base import Base
from acd.models.company import Company


class Job(Base):
    """
    Entidade de domínio para uma vaga.

    Representa uma oportunidade de emprego vinculada a uma empresa
    cadastrada no sistema.
    """

    __tablename__ = "jobs"

    __table_args__ = (
        Index("ix_jobs_company_id", "company_id"),
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_application_date", "application_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String(200),
        nullable=True,
        default="",
    )

    work_model: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default="",
    )

    employment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default="",
    )

    salary_min: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    salary_max: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=True,
        default="",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default="Nova",
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        default="",
    )

    job_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default="",
    )

    recruiter: Mapped[str] = mapped_column(
        String(200),
        nullable=True,
        default="",
    )

    application_deadline: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    application_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    notes: Mapped[str] = mapped_column(
        String(1000),
        nullable=True,
        default="",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    company: Mapped[Company] = relationship(
        "Company",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return (
            f"<Job(id={self.id}, "
            f"title='{self.title}', "
            f"company_id={self.company_id}, "
            f"status='{self.status}')>"
        )

