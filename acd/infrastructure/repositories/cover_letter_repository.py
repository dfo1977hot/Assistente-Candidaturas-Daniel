from __future__ import annotations

from sqlalchemy import or_, select

from acd.database import database as database_module
from acd.domain.entities.cover_letter_version import CoverLetterVersion


class CoverLetterRepository:
    """Persistência de cartas de apresentação versionadas."""

    def create(self, letter: CoverLetterVersion) -> CoverLetterVersion:
        with database_module.SessionLocal() as session:
            session.add(letter)
            session.commit()
            session.refresh(letter)
            return letter

    def update(self, letter: CoverLetterVersion) -> CoverLetterVersion:
        with database_module.SessionLocal() as session:
            merged = session.merge(letter)
            session.commit()
            session.refresh(merged)
            return merged

    def get_by_id(self, letter_id: int) -> CoverLetterVersion | None:
        with database_module.SessionLocal() as session:
            return session.get(CoverLetterVersion, letter_id)

    def get_all(self) -> list[CoverLetterVersion]:
        with database_module.SessionLocal() as session:
            stmt = select(CoverLetterVersion).order_by(
                CoverLetterVersion.created_at.desc()
            )
            return list(session.scalars(stmt).all())

    def search(self, query: str) -> list[CoverLetterVersion]:
        normalized = query.strip()
        if not normalized:
            return self.get_all()
        pattern = f"%{normalized}%"
        with database_module.SessionLocal() as session:
            stmt = (
                select(CoverLetterVersion)
                .where(
                    or_(
                        CoverLetterVersion.subject.ilike(pattern),
                        CoverLetterVersion.content.ilike(pattern),
                        CoverLetterVersion.notes.ilike(pattern),
                        CoverLetterVersion.letter_type.ilike(pattern),
                        CoverLetterVersion.status.ilike(pattern),
                    )
                )
                .order_by(CoverLetterVersion.created_at.desc())
            )
            return list(session.scalars(stmt).all())

    def delete(self, letter_id: int) -> bool:
        with database_module.SessionLocal() as session:
            entity = session.get(CoverLetterVersion, letter_id)
            if entity is None:
                return False
            session.delete(entity)
            session.commit()
            return True

    def versions_for_context(
        self,
        *,
        job_id: int | None,
        curriculum_id: int,
    ) -> list[CoverLetterVersion]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(CoverLetterVersion)
                .where(
                    CoverLetterVersion.job_id == job_id,
                    CoverLetterVersion.curriculum_id == curriculum_id,
                )
                .order_by(CoverLetterVersion.created_at.desc())
            )
            return list(session.scalars(stmt).all())

    def latest_application_id_for_job(self, job_id: int) -> int | None:
        from acd.domain.entities.application import Application

        with database_module.SessionLocal() as session:
            stmt = (
                select(Application.id)
                .where(Application.job_id == job_id)
                .order_by(Application.created_at.desc())
                .limit(1)
            )
            value = session.scalar(stmt)
            return None if value is None else int(value)
