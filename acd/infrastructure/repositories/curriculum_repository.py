from __future__ import annotations

from sqlalchemy import select

from acd.application.structured_resume_snapshot import (
    StructuredResumeSnapshot,
    StructuredResumeSnapshotCodec,
)
from acd.database import database as database_module
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.curriculum_version import CurriculumVersion
from acd.infrastructure.database.dependency_delete import (
    ExtraDependency,
    delete_with_dependencies,
)


class CurriculumRepository:
    """Repositório para currículos e versões."""

    def create(
        self,
        curriculum: Curriculum,
        structured_resume: StructuredResumeSnapshot | None = None,
    ) -> Curriculum:
        """Persist a curriculum, optionally with a validated structured snapshot."""
        if structured_resume is not None:
            curriculum.structured_content_json = StructuredResumeSnapshotCodec().dumps(
                structured_resume
            )
        with database_module.SessionLocal() as session:
            session.add(curriculum)
            session.commit()
            session.refresh(curriculum)
            return curriculum

    def update(
        self,
        curriculum: Curriculum,
        structured_resume: StructuredResumeSnapshot | None = None,
    ) -> Curriculum:
        """Update a curriculum, optionally replacing its validated snapshot."""
        if structured_resume is not None:
            curriculum.structured_content_json = StructuredResumeSnapshotCodec().dumps(
                structured_resume
            )
        with database_module.SessionLocal() as session:
            session.add(curriculum)
            session.commit()
            session.refresh(curriculum)
            return curriculum

    def delete(self, curriculum_id: int, *, delete_linked: bool = False) -> bool:
        with database_module.SessionLocal() as session:
            if delete_linked:
                return delete_with_dependencies(
                    session,
                    table_name="curricula",
                    primary_key="id",
                    value=curriculum_id,
                    extra_dependencies=(ExtraDependency("applications", "curriculum_id"),),
                )
            entity = session.get(Curriculum, curriculum_id)
            if entity is None:
                return False
            session.delete(entity)
            session.commit()
            return True

    def get_by_id(self, curriculum_id: int) -> Curriculum | None:
        with database_module.SessionLocal() as session:
            return session.get(Curriculum, curriculum_id)

    def get_all(self) -> list[Curriculum]:
        with database_module.SessionLocal() as session:
            stmt = select(Curriculum).order_by(Curriculum.name.asc())
            return list(session.scalars(stmt).all())

    def get_default(self) -> Curriculum | None:
        with database_module.SessionLocal() as session:
            stmt = select(Curriculum).where(Curriculum.is_default.is_(True))
            return session.scalar(stmt)

    def get_versions(self, curriculum_id: int) -> list[CurriculumVersion]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(CurriculumVersion)
                .where(CurriculumVersion.curriculum_id == curriculum_id)
                .order_by(CurriculumVersion.created_at.asc())
            )
            return list(session.scalars(stmt).all())

    def search(self, query: str) -> list[Curriculum]:
        with database_module.SessionLocal() as session:
            stmt = select(Curriculum).where(
                Curriculum.name.ilike(f"%{query}%")
                | Curriculum.description.ilike(f"%{query}%")
                | Curriculum.language.ilike(f"%{query}%")
            )
            return list(session.scalars(stmt).all())

    def exists(self, curriculum_id: int) -> bool:
        with database_module.SessionLocal() as session:
            return session.get(Curriculum, curriculum_id) is not None

    def create_version(self, curriculum_id: int, version: CurriculumVersion) -> CurriculumVersion:
        with database_module.SessionLocal() as session:
            session.add(version)
            session.commit()
            session.refresh(version)
            return version
