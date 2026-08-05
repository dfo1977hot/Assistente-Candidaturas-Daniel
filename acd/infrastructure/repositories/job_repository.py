from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from acd.database import database as database_module
from acd.domain.entities.job import Job


class JobRepository:
    """Repositório responsável pela persistência de vagas."""

    def create(self, job: Job) -> Job:
        with database_module.SessionLocal() as session:
            try:
                session.add(job)
                session.commit()
                session.refresh(job)
                return job
            except Exception:
                session.rollback()
                raise

    def update(self, job: Job) -> Job:
        with database_module.SessionLocal() as session:
            try:
                job = session.merge(job)
                session.commit()
                session.refresh(job)
                return job
            except Exception:
                session.rollback()
                raise

    def delete(self, job_id: int) -> bool:
        with database_module.SessionLocal() as session:
            try:
                job = session.get(Job, job_id)

                if job is None:
                    return False

                session.delete(job)
                session.commit()
                return True

            except Exception:
                session.rollback()
                raise

    def get_by_id(self, job_id: int) -> Job | None:
        with database_module.SessionLocal() as session:
            stmt = select(Job).options(joinedload(Job.company)).where(Job.id == job_id)
            return session.scalar(stmt)

    def get_all(self) -> list[Job]:
        with database_module.SessionLocal() as session:
            stmt = select(Job).options(joinedload(Job.company)).order_by(Job.created_at.desc())
            return list(session.scalars(stmt).all())

    def search(self, query: str) -> list[Job]:
        with database_module.SessionLocal() as session:
            search_text = f"%{query}%"

            stmt = (
                select(Job)
                .options(joinedload(Job.company))
                .where(
                    or_(
                        Job.title.ilike(search_text),
                        Job.recruiter.ilike(search_text),
                        Job.source.ilike(search_text),
                        Job.notes.ilike(search_text),
                    )
                )
                .order_by(Job.created_at.desc())
            )

            return list(session.scalars(stmt).all())

    def filter(
        self,
        *,
        company_id: int | None = None,
        status: str | None = None,
        work_model: str | None = None,
        employment_type: str | None = None,
    ) -> list[Job]:
        with database_module.SessionLocal() as session:
            stmt = select(Job).options(joinedload(Job.company))

            if company_id is not None:
                stmt = stmt.where(Job.company_id == company_id)

            if status:
                stmt = stmt.where(Job.status == status)

            if work_model:
                stmt = stmt.where(Job.work_model == work_model)

            if employment_type:
                stmt = stmt.where(Job.employment_type == employment_type)

            stmt = stmt.order_by(Job.created_at.desc())

            return list(session.scalars(stmt).all())

    def list_by_company(self, company_id: int) -> list[Job]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Job)
                .options(joinedload(Job.company))
                .where(Job.company_id == company_id)
                .order_by(Job.created_at.desc())
            )

            return list(session.scalars(stmt).all())

    def list_by_status(self, status: str) -> list[Job]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Job)
                .options(joinedload(Job.company))
                .where(Job.status == status)
                .order_by(Job.created_at.desc())
            )

            return list(session.scalars(stmt).all())

    def list_recent(self, limit: int = 20) -> list[Job]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Job)
                .options(joinedload(Job.company))
                .order_by(Job.created_at.desc())
                .limit(limit)
            )

            return list(session.scalars(stmt).all())

    def exists(self, job_id: int) -> bool:
        with database_module.SessionLocal() as session:
            return session.get(Job, job_id) is not None

    def count(self) -> int:
        with database_module.SessionLocal() as session:
            stmt = select(func.count(Job.id))
            return session.scalar(stmt) or 0
