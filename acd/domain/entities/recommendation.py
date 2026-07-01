from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class Recommendation(Base):
    """Recomendação gerada a partir de uma comparação ATS."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    score_id: Mapped[int] = mapped_column(ForeignKey("ats_scores.id"), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="rule")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
