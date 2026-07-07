from __future__ import annotations
from acd.core.datetime_utils import utc_now

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class ScoreDetail(Base):
    """Detalhamento do score por critério."""

    __tablename__ = "score_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    score_id: Mapped[int] = mapped_column(ForeignKey("ats_scores.id"), nullable=False)
    criterion: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
