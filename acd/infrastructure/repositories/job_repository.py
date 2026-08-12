from __future__ import annotations

import re

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from acd.database import database as database_module
from acd.domain.entities.job import Job
from acd.infrastructure.database.dependency_delete import delete_with_dependencies


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

    def delete(self, job_id: int, *, delete_linked: bool = False) -> bool:
        with database_module.SessionLocal() as session:
            if delete_linked:
                return delete_with_dependencies(
                    session,
                    table_name="jobs",
                    primary_key="id",
                    value=job_id,
                )
            entity = session.get(Job, job_id)
            if entity is None:
                return False
            session.delete(entity)
            session.commit()
            return True

    def get_by_id(self, job_id: int) -> Job | None:
        with database_module.SessionLocal() as session:
            stmt = select(Job).options(joinedload(Job.company)).where(Job.id == job_id)
            return session.scalar(stmt)


    def get_linkedin_job_ids(self) -> set[str]:
        """Return numeric LinkedIn identifiers from already persisted job URLs."""
        with database_module.SessionLocal() as session:
            stmt = select(Job.job_url).where(
                Job.source.ilike("LinkedIn"),
                Job.job_url.is_not(None),
                Job.job_url != "",
            )
            urls = session.scalars(stmt).all()

        identifiers: set[str] = set()
        for url in urls:
            match = re.search(
                r"(?:currentJobId=|/jobs/view/(?:[^/?]+-)?)(\d{6,})",
                url or "",
            )
            if match:
                identifiers.add(match.group(1))
        return identifiers

    def get_by_url(self, job_url: str) -> Job | None:
        """Retorna a vaga cadastrada com a URL informada."""
        normalized = job_url.strip()
        if not normalized:
            return None
        with database_module.SessionLocal() as session:
            stmt = (
                select(Job)
                .options(joinedload(Job.company))
                .where(Job.job_url == normalized)
            )
            return session.scalar(stmt)

    def get_by_linkedin_job_id(self, linkedin_job_id: str) -> Job | None:
        """Return a LinkedIn job matching its numeric identifier."""
        normalized = linkedin_job_id.strip()
        if not normalized:
            return None
        with database_module.SessionLocal() as session:
            patterns = (
                f"%/jobs/view/%{normalized}%",
                f"%currentJobId={normalized}%",
            )
            stmt = (
                select(Job)
                .options(joinedload(Job.company))
                .where(or_(*(Job.job_url.like(pattern) for pattern in patterns)))
            )
            return session.scalar(stmt)

    def url_exists(self, job_url: str, *, exclude_job_id: int | None = None) -> bool:
        """Informa se a URL já está vinculada a outra vaga."""
        normalized = job_url.strip()
        if not normalized:
            return False
        with database_module.SessionLocal() as session:
            stmt = select(func.count(Job.id)).where(Job.job_url == normalized)
            if exclude_job_id is not None:
                stmt = stmt.where(Job.id != exclude_job_id)
            return bool(session.scalar(stmt) or 0)

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
                        Job.recruiter_email.ilike(search_text),
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
