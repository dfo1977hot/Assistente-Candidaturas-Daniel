from __future__ import annotations
from acd.core.datetime_utils import utc_now

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acd.domain.entities.application import Application
from acd.models.base import Base


class Interview(Base):
    """Entidade de domínio para entrevistas."""

    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)
    interview_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interview_type: Mapped[str] = mapped_column(String(50), nullable=False)
    interviewer: Mapped[str] = mapped_column(String(200), nullable=True, default="")
    interviewer_email: Mapped[str] = mapped_column(String(200), nullable=True, default="")
    meeting_link: Mapped[str] = mapped_column(String(300), nullable=True, default="")
    location: Mapped[str] = mapped_column(String(200), nullable=True, default="")
    duration: Mapped[str] = mapped_column(String(50), nullable=True, default="")
    notes: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    feedback: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    result: Mapped[str] = mapped_column(String(50), nullable=True, default="Agendada")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    application: Mapped[Application] = relationship("Application")

    def __repr__(self) -> str:
        return f"<Interview {self.id}>"
