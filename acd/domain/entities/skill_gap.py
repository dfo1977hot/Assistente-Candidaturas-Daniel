from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class SkillGap(Base):
    """Registro de lacunas identificadas em uma comparação."""

    __tablename__ = "skill_gaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    score_id: Mapped[int] = mapped_column(ForeignKey("ats_scores.id"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gap_type: Mapped[str] = mapped_column(String(50), nullable=False, default="missing")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
