"""Integration tests for the interview persistence contract."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import acd.database.database as database_module
from acd.domain.entities.application import Application
from acd.domain.entities.interview import Interview
from acd.domain.entities.job import Job
from acd.infrastructure.repositories.interview_repository import InterviewRepository
from acd.models.base import Base
from acd.models.company import Company


@pytest.fixture(autouse=True)
def override_database(tmp_path, monkeypatch):
    """Provide a closed, file-backed SQLite database for repository tests."""

    engine = create_engine(f"sqlite:///{tmp_path / 'interviews.db'}", future=True)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(database_module, "SessionLocal", session_local)
    Base.metadata.create_all(bind=engine)
    try:
        yield session_local
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _create_application(session_local) -> Application:
    session = session_local()
    company = Company(name="Acme", city="Sao Paulo")
    session.add(company)
    session.flush()
    job = Job(company_id=company.id, title="Python Engineer")
    session.add(job)
    session.flush()
    application = Application(job_id=job.id, company_id=company.id)
    session.add(application)
    session.commit()
    session.refresh(application)
    session.close()
    return application


def _interview(application_id: int, interview_date: datetime, **kwargs: str) -> Interview:
    return Interview(
        application_id=application_id,
        interview_date=interview_date,
        interview_type=kwargs.get("interview_type", "RH"),
        interviewer=kwargs.get("interviewer", "Ana"),
        notes=kwargs.get("notes", "Discuss Python experience"),
        result=kwargs.get("result", "Agendada"),
    )


def test_interview_repository_filters_searches_and_orders_interviews(override_database) -> None:
    """Repository applies all filters and returns chronological query results."""

    application = _create_application(override_database)
    repository = InterviewRepository()
    now = datetime.now().replace(microsecond=0)
    later = repository.create(
        _interview(application.id, now + timedelta(days=2), interviewer="Bruno", result="Realizada")
    )
    earlier = repository.create(
        _interview(application.id, now + timedelta(days=1), notes="Culture interview")
    )

    assert [item.id for item in repository.get_all()] == [earlier.id, later.id]
    assert [item.id for item in repository.search("culture")] == [earlier.id]
    assert [item.id for item in repository.search("bruno")] == [later.id]
    assert [item.id for item in repository.filter(interview_type="RH", result="Agendada")] == [
        earlier.id
    ]
    assert [
        item.id
        for item in repository.filter(
            period_start=now + timedelta(hours=12), period_end=now + timedelta(days=1, hours=12)
        )
    ] == [earlier.id]


def test_interview_repository_handles_absence_upcoming_results_and_statistics(override_database) -> None:
    """Repository distinguishes missing records and computes date-based agenda summaries."""

    application = _create_application(override_database)
    repository = InterviewRepository()
    now = datetime.now().replace(microsecond=0)
    today_date = now.date()
    past = repository.create(_interview(application.id, now - timedelta(days=1), result="Realizada"))
    today = repository.create(
        _interview(application.id, datetime.combine(today_date, datetime.min.time()))
    )
    upcoming = repository.create(
        _interview(application.id, datetime.combine(today_date + timedelta(days=1), datetime.min.time()))
    )

    assert repository.get_by_id(99999) is None
    assert [item.id for item in repository.get_today()] == [today.id]
    assert [item.id for item in repository.get_next(limit=1)] == [upcoming.id]
    assert repository.get_statistics() == {"total": 3, "today": 1, "week": 2}

    today.notes = "Confirmed"
    assert repository.update(today).notes == "Confirmed"
    assert repository.delete(past.id) is True
    assert repository.delete(past.id) is False
    assert repository.get_by_id(upcoming.id).id == upcoming.id
