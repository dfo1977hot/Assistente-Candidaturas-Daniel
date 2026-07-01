from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.job import Job


class JobRepository:
    """Repositório para persistência de vagas."""

    def create(self, job: Job) -> Job:
        with database_module.SessionLocal() as session:
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def update(self, job: Job) -> Job:
        with database_module.SessionLocal() as session:
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def delete(self, job_id: int) -> bool:
        with database_module.SessionLocal() as session:
            job = session.get(Job, job_id)
            if job is None:
                return False
            session.delete(job)
            session.commit()
            return True

    def get_by_id(self, job_id: int) -> Optional[Job]:
        with database_module.SessionLocal() as session:
            return session.get(Job, job_id)

    def get_all(self) -> list[Job]:
        with database_module.SessionLocal() as session:
            stmt = select(Job).order_by(Job.created_at.desc())
            return list(session.scalars(stmt).all())

    def search(self, query: str) -> list[Job]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Job)
                .where(Job.title.ilike(f"%{query}%"))
                .order_by(Job.created_at.desc())
            )
            return list(session.scalars(stmt).all())

    def filter(self, *, company_id: Optional[int] = None, status: Optional[str] = None, work_model: Optional[str] = None, employment_type: Optional[str] = None) -> list[Job]:
        with database_module.SessionLocal() as session:
            stmt = select(Job)
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

    def exists(self, job_id: int) -> bool:
        with database_module.SessionLocal() as session:
            return session.get(Job, job_id) is not None

    def count(self) -> int:
        with database_module.SessionLocal() as session:
            return session.query(Job).count()
