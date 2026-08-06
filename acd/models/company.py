from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from acd.core.datetime_utils import utc_now
from acd.models.base import Base


class Company(Base):
    """Entidade de domínio para uma empresa."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(250), nullable=False, default="")
    tax_id: Mapped[str] = mapped_column(String(20), nullable=False, default="", index=True)
    registration_status: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    segment: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    address: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    company_size: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    website: Mapped[str] = mapped_column(String(300), nullable=True, default="")
    linkedin_url: Mapped[str] = mapped_column(String(300), nullable=True, default="")
    data_source: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    source_reference: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    data_retrieved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<Company {self.name}>"
