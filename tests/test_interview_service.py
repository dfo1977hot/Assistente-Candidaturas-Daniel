import os
import tempfile

import pytest

from acd.infrastructure.repositories.application_repository import ApplicationRepository
from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.infrastructure.repositories.interview_repository import InterviewRepository
from acd.infrastructure.repositories.job_repository import JobRepository
from acd.services.application_service import ApplicationService
from acd.services.company_service import CompanyService
from acd.services.interview_service import InterviewService
from acd.services.job_service import JobService


@pytest.fixture
def interview_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-interview-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd.db")
    monkeypatch.setattr(
        "acd.database.database.DATABASE_URL",
        f"sqlite:///{db_path}",
    )

    import acd.database.database as database_module

    database_module.engine.dispose()
    database_module.engine = database_module.create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        future=True,
    )
    database_module.SessionLocal = database_module.sessionmaker(
        bind=database_module.engine,
        autoflush=False,
        autocommit=False,
    )

    from acd.models.base import Base

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    company_service = CompanyService(repository=CompanyRepository())
    company_id = company_service.create_company(name="Acme", city="São Paulo").id
    job_service = JobService(repository=JobRepository())
    job_id = job_service.create_job(company_id=company_id, title="Python Developer").id
    application_service = ApplicationService(repository=ApplicationRepository())
    application = application_service.create_application(job_id=job_id, company_id=company_id)

    yield InterviewService(repository=InterviewRepository()), application.id

    Base.metadata.drop_all(bind=database_module.engine)


def test_interview_service_creates_and_lists_interviews(interview_setup):
    interview_service, application_id = interview_setup

    created = interview_service.create_interview(
        application_id=application_id,
        interview_date="2026-07-10 10:00:00",
        interview_type="RH",
    )

    assert created.id is not None
    assert len(interview_service.list_interviews()) == 1


def test_interview_service_detects_upcoming_reminders(interview_setup):
    interview_service, application_id = interview_setup

    interview_service.create_interview(
        application_id=application_id,
        interview_date="2099-07-01 10:00:00",
        interview_type="RH",
    )

    reminders = interview_service.get_reminders(hours=24)
    assert reminders == []
