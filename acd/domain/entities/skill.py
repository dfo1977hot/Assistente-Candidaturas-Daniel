from __future__ import annotations
from acd.core.datetime_utils import utc_now

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acd.models.base import Base

if TYPE_CHECKING:
    from acd.domain.entities.skill import Skill


class SkillCategory(Base):
    """Categoria estrutural para organizar competências."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True, default="")
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    parent: Mapped[SkillCategory | None] = relationship(back_populates="children", remote_side=[id])
    children: Mapped[list[SkillCategory]] = relationship(back_populates="parent")


class Skill(Base):
    """Catálogo reutilizável de competências."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    description: Mapped[str] = mapped_column(String(1000), nullable=True, default="")
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    aliases: Mapped[list[SkillAlias]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
    weights: Mapped[list[SkillWeight]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Skill {self.name}>"


class SkillAlias(Base):
    """Sinônimos e aliases de uma competência."""

    __tablename__ = "skill_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    alias_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    skill: Mapped[Skill] = relationship(back_populates="aliases")


class SkillRelation(Base):
    """Relacionamentos entre competências."""

    __tablename__ = "skill_relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    child_skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Relacionado")
    strength: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class SkillWeight(Base):
    """Pesos configuráveis associados a uma competência."""

    __tablename__ = "skill_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source: Mapped[str] = mapped_column(String(100), nullable=True, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    skill: Mapped[Skill] = relationship(back_populates="weights")
