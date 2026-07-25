"""Integration tests for the application persistence contract."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import acd.database.database as database_module
from acd.domain.entities.application import Application
from acd.domain.entities.job import Job
from acd.infrastructure.repositories.application_repository import ApplicationRepository
from acd.models.base import Base
from acd.models.company import Company


@pytest.fixture(autouse=True)
def override_database(tmp_path, monkeypatch):
    """Provide a closed, file-backed SQLite database for repository tests."""

    engine = create_engine(f"sqlite:///{tmp_path / 'applications.db'}", future=True)
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


def _application(job: Job, **kwargs: object) -> Application:
    return Application(
        job_id=job.id,
        company_id=job.company_id,
        status=kwargs.get("status", "Rascunho"),
        application_date=kwargs.get("application_date"),
        application_channel=kwargs.get("application_channel", "LinkedIn"),
        notes=kwargs.get("notes", "Python and SQL profile"),
        feedback=kwargs.get("feedback", ""),
    )


def test_application_repository_persists_queries_filters_and_updates(override_database) -> None:
    """Applications support joined reads, filtering, search, updates, and status changes."""

    job = _create_job(override_database)
    repository = ApplicationRepository()
    older = repository.create(
        _application(job, application_date=date(2026, 1, 10), status="Aplicada")
    )
    newer = repository.create(
        _application(
            job,
            application_date=date(2026, 1, 12),
            status="Encerrada",
            application_channel="Indicação",
            feedback="No response",
        )
    )

    loaded = repository.get_by_id(older.id)
    assert loaded is not None
    assert loaded.job.title == "Python Engineer"
    assert loaded.company.name == "Acme"
    assert [item.id for item in repository.get_all()] == [newer.id, older.id]
    assert [item.id for item in repository.search("response")] == [newer.id]
    assert [item.id for item in repository.filter(status="Aplicada")] == [older.id]
    assert [item.id for item in repository.filter(company_id=job.company_id)] == [newer.id, older.id]
    assert [item.id for item in repository.filter(channel="Indicação")] == [newer.id]

    older.notes = "Updated profile"
    assert repository.update(older).notes == "Updated profile"
    assert repository.change_status(older.id, "Em Triagem").status == "Em Triagem"
    assert repository.change_status(99999, "Aplicada") is None


def test_application_repository_tracks_events_statistics_and_deletion(override_database) -> None:
    """Events, aggregate counts, missing records, and deletion follow repository contracts."""

    job = _create_job(override_database)
    repository = ApplicationRepository()
    active = repository.create(_application(job, application_date=date(2026, 2, 1)))
    closed = repository.create(
        _application(job, application_date=date(2026, 2, 2), status="Encerrada")
    )

    first_event = repository.add_event(active.id, "created", "Application created")
    second_event = repository.add_event(active.id, "updated", "Application updated")

    assert [item.id for item in repository.get_followups(active.id)] == [second_event.id, first_event.id]
    assert repository.get_statistics() == {"total": 2, "active": 1}
    assert repository.count() == 2
    assert repository.get_by_id(99999) is None
    assert repository.delete(closed.id) is True
    assert repository.delete(closed.id) is False
    assert repository.count() == 1
