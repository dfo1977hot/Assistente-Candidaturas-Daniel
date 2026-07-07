from __future__ import annotations
from acd.core.datetime_utils import utc_now

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class CareerGoal(Base):
    """Career objective definition and tracking."""

    __tablename__ = "career_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_role: Mapped[str] = mapped_column(String(200), nullable=False)
    target_industry: Mapped[str] = mapped_column(String(200), nullable=False)
    target_location: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    target_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    target_work_model: Mapped[str] = mapped_column(String(50), nullable=False, default="hybrid")
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_compatibility: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
