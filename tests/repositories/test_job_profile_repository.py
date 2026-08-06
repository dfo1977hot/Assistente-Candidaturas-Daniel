"""Integration tests for the job profile persistence contract."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import acd.database.database as database_module
from acd.domain.entities.job import Job
from acd.domain.entities.job_profile import JobProfile
from acd.infrastructure.repositories.job_profile_repository import JobProfileRepository
from acd.models.base import Base
from acd.models.company import Company


@pytest.fixture(autouse=True)
def override_database(tmp_path, monkeypatch):
    """Provide a closed, file-backed SQLite database for repository tests."""

    engine = create_engine(f"sqlite:///{tmp_path / 'job_profiles.db'}", future=True)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(database_module, "SessionLocal", session_local)
    Base.metadata.create_all(bind=engine)
    try:
        yield session_local
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _create_job(session_local) -> Job:
    session = session_local()
    company = Company(name="Acme", city="Sao Paulo")
    session.add(company)
    session.flush()
    job = Job(company_id=company.id, title="Python Engineer")
    session.add(job)
    session.commit()
    session.refresh(job)
    session.close()
    return job


def test_job_profile_repository_persists_searches_updates_and_deletes(override_database) -> None:
    """A profile can be persisted, queried by text, updated, and removed."""

    job = _create_job(override_database)
    repository = JobProfileRepository()
    profile = repository.create(
        JobProfile(
            job_id=job.id,
            raw_description="Python and Docker required",
            skills="Python,Docker",
        )
    )

    assert repository.get_by_job(job.id).id == profile.id
    assert [item.id for item in repository.search("docker")] == [profile.id]

    profile.skills = "Python,Docker,SQL"
    updated = repository.update(profile)

    assert updated.skills == "Python,Docker,SQL"
    assert repository.delete(profile.id) is True
    assert repository.delete(profile.id) is False
    assert repository.get_by_job(job.id) is None


def test_job_profile_repository_reports_statistics_for_profiles_with_and_without_skills(
    override_database,
) -> None:
    """Statistics count every profile while retaining only declared skill values."""

    job = _create_job(override_database)
    repository = JobProfileRepository()
    repository.create(JobProfile(job_id=job.id, raw_description="Python role", skills="Python,Docker"))
    repository.create(JobProfile(job_id=job.id, raw_description="Generalist role", skills=""))

    assert repository.get_statistics() == {
        "total_profiles": 2,
        "top_skills": ["Python", "Docker"],
    }
