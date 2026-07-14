from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class ATSScore(Base):
    """Registro persistido de um cálculo de aderência currículo-vaga."""

    __tablename__ = "ats_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"), nullable=True)
    curriculum_id: Mapped[int | None] = mapped_column(ForeignKey("curricula.id"), nullable=True)
    job_profile_id: Mapped[int | None] = mapped_column(ForeignKey("job_profiles.id"), nullable=True)
    total_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
