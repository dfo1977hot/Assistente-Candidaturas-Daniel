from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class Company(Base):
    """Entidade de domínio para uma empresa."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    city: Mapped[str] = mapped_column(String(100), nullable=False)

    website: Mapped[str] = mapped_column(String(300), nullable=True, default="")

    notes: Mapped[str] = mapped_column(String(1000), nullable=True, default="")

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

    def __repr__(self) -> str:
        return f"<Company {self.name}>"