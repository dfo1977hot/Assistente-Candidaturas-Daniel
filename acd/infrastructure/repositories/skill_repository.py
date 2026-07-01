from __future__ import annotations

from typing import Any

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.skill import Skill, SkillAlias, SkillRelation, SkillWeight


class SkillRepository:
    """Repositório para persistência e consulta do catálogo de competências."""

    def create(self, skill: Skill) -> Skill:
        with database_module.SessionLocal() as session:
            session.add(skill)
            session.commit()
            session.refresh(skill)
            return skill

    def update(self, skill: Skill) -> Skill:
        with database_module.SessionLocal() as session:
            session.add(skill)
            session.commit()
            session.refresh(skill)
            return skill

    def delete(self, skill_id: int) -> bool:
        with database_module.SessionLocal() as session:
            skill = session.get(Skill, skill_id)
            if skill is None:
                return False
            session.delete(skill)
            session.commit()
            return True

    def get_by_id(self, skill_id: int) -> Skill | None:
        with database_module.SessionLocal() as session:
            return session.get(Skill, skill_id)

    def get_all(self) -> list[Skill]:
        with database_module.SessionLocal() as session:
            stmt = select(Skill).order_by(Skill.name.asc())
            return list(session.scalars(stmt).all())

    def search(self, query: str) -> list[Skill]:
        with database_module.SessionLocal() as session:
            stmt = select(Skill).where(Skill.name.ilike(f"%{query}%"))
            return list(session.scalars(stmt).all())

    def add_alias(self, skill_id: int, alias_name: str) -> SkillAlias:
        with database_module.SessionLocal() as session:
            skill = session.get(Skill, skill_id)
            if skill is None:
                raise ValueError("Competência não encontrada")
            alias = SkillAlias(skill_id=skill.id, alias_name=alias_name)
            session.add(alias)
            session.commit()
            session.refresh(alias)
            return alias

    def get_aliases(self, skill_id: int) -> list[SkillAlias]:
        with database_module.SessionLocal() as session:
            stmt = select(SkillAlias).where(SkillAlias.skill_id == skill_id)
            return list(session.scalars(stmt).all())

    def add_relation(self, relation: SkillRelation) -> SkillRelation:
        with database_module.SessionLocal() as session:
            session.add(relation)
            session.commit()
            session.refresh(relation)
            return relation

    def get_relations(self) -> list[SkillRelation]:
        with database_module.SessionLocal() as session:
            stmt = select(SkillRelation).order_by(SkillRelation.created_at.asc())
            return list(session.scalars(stmt).all())

    def get_tree(self) -> list[dict[str, Any]]:
        with database_module.SessionLocal() as session:
            skills = list(session.scalars(select(Skill).order_by(Skill.created_at.asc())).all())
            return [
                {
                    "id": skill.id,
                    "name": skill.name,
                    "category": skill.category,
                    "weight": skill.weight,
                    "description": skill.description,
                }
                for skill in skills
            ]

    def find_similar(self, query: str) -> list[Skill]:
        with database_module.SessionLocal() as session:
            stmt = select(Skill).where(Skill.name.ilike(f"%{query}%"))
            return list(session.scalars(stmt).all())

    def set_weight(self, skill_id: int, weight: float, source: str = "manual") -> SkillWeight:
        with database_module.SessionLocal() as session:
            skill = session.get(Skill, skill_id)
            if skill is None:
                raise ValueError("Competência não encontrada")
            weight_entry = SkillWeight(skill_id=skill.id, weight=weight, source=source)
            session.add(weight_entry)
            session.commit()
            session.refresh(weight_entry)
            return weight_entry

    def count(self) -> int:
        with database_module.SessionLocal() as session:
            return session.query(Skill).count()

    def count_relations(self) -> int:
        with database_module.SessionLocal() as session:
            return session.query(SkillRelation).count()

    def count_categories(self) -> int:
        with database_module.SessionLocal() as session:
            return session.query(Skill).filter(Skill.category != "").count()
