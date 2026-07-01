from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acd.models.base import Base
from acd.domain.entities.curriculum import Curriculum


class CurriculumVersion(Base):
    """Versão física de um currículo."""

    __tablename__ = "curriculum_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    curriculum_id: Mapped[int] = mapped_column(ForeignKey("curricula.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(300), nullable=True, default="")
    file_path: Mapped[str] = mapped_column(String(500), nullable=True, default="")
    file_type: Mapped[str] = mapped_column(String(50), nullable=True, default="")
    checksum: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    curriculum: Mapped[Curriculum] = relationship(back_populates="versions")

    def __repr__(self) -> str:
        return f"<CurriculumVersion {self.version}>"
