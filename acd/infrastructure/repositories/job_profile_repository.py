from __future__ import annotations

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.job_profile import JobProfile


class JobProfileRepository:
    """Repositório para perfis estruturados de vagas."""

    def create(self, profile: JobProfile) -> JobProfile:
        with database_module.SessionLocal() as session:
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return profile

    def update(self, profile: JobProfile) -> JobProfile:
        with database_module.SessionLocal() as session:
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return profile

    def delete(self, profile_id: int) -> bool:
        with database_module.SessionLocal() as session:
            profile = session.get(JobProfile, profile_id)
            if profile is None:
                return False
            session.delete(profile)
            session.commit()
            return True

    def get_by_job(self, job_id: int) -> JobProfile | None:
        with database_module.SessionLocal() as session:
            stmt = select(JobProfile).where(JobProfile.job_id == job_id)
            return session.scalar(stmt)

    def search(self, query: str) -> list[JobProfile]:
        with database_module.SessionLocal() as session:
            stmt = select(JobProfile).where(JobProfile.raw_description.ilike(f"%{query}%"))
            return list(session.scalars(stmt).all())

    def get_statistics(self) -> dict[str, object]:
        with database_module.SessionLocal() as session:
            profiles = list(session.query(JobProfile).all())
            top_skills = []
            for profile in profiles:
                top_skills.extend(profile.skills.split(",") if profile.skills else [])
            return {"total_profiles": len(profiles), "top_skills": top_skills[:10]}
