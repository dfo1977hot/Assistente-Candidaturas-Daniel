import os
import tempfile

import pytest

from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.infrastructure.repositories.job_repository import JobRepository
from acd.services.company_service import CompanyService
from acd.services.job_service import JobService


@pytest.fixture
def service_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-job-", dir=".")
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
    company = company_service.create_company(name="Acme", city="São Paulo")
    yield JobService(repository=JobRepository()), company.id

    Base.metadata.drop_all(bind=database_module.engine)


def test_job_service_creates_and_filters_jobs(service_setup):
    job_service, company_id = service_setup

    created = job_service.create_job(company_id=company_id, title="Python Developer")

    assert created.id is not None
    assert job_service.count_jobs() == 1
    assert job_service.filter_jobs(company_id=company_id)[0].title == "Python Developer"


def test_job_service_updates_and_deletes_job(service_setup):
    job_service, company_id = service_setup

    created = job_service.create_job(company_id=company_id, title="Python Developer")
    updated = job_service.update_job(
        created.id, company_id=company_id, title="Senior Python Developer"
    )

    assert updated is not None
    assert updated.title == "Senior Python Developer"
    assert job_service.delete_job(created.id) is True
    assert job_service.count_jobs() == 0
