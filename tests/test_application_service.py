import os
import tempfile

import pytest

from acd.infrastructure.repositories.application_repository import ApplicationRepository
from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.infrastructure.repositories.job_repository import JobRepository
from acd.services.application_service import ApplicationService
from acd.services.company_service import CompanyService
from acd.services.job_service import JobService


@pytest.fixture
def service_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-application-", dir=".")
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

    yield ApplicationService(repository=ApplicationRepository()), job_id, company_id

    Base.metadata.drop_all(bind=database_module.engine)


def test_application_service_creates_and_changes_status(service_setup):
    application_service, job_id, company_id = service_setup

    created = application_service.create_application(job_id=job_id, company_id=company_id)

    assert created.id is not None
    assert application_service.get_statistics()["total"] == 1
    updated = application_service.change_status(created.id, "Pronta para Aplicação")
    assert updated is not None
    assert updated.status == "Pronta para Aplicação"


def test_application_service_rejects_invalid_status_transition(service_setup):
    application_service, job_id, company_id = service_setup

    created = application_service.create_application(job_id=job_id, company_id=company_id)

    with pytest.raises(ValueError):
        application_service.change_status(created.id, "Contratada")


def test_application_service_updates_and_deletes_application(service_setup):
    application_service, job_id, company_id = service_setup

    created = application_service.create_application(job_id=job_id, company_id=company_id)
    application_service.change_status(created.id, "Pronta para Aplicação")
    updated = application_service.update_application(
        created.id,
        job_id=job_id,
        company_id=company_id,
        status="Aplicada",
    )

    assert updated is not None
    assert updated.status == "Aplicada"
    assert application_service.delete_application(created.id) is True
    assert application_service.get_statistics()["total"] == 0


def test_application_service_creates_followup_event(service_setup):
    application_service, job_id, company_id = service_setup

    created = application_service.create_application(job_id=job_id, company_id=company_id)
    followups = application_service.get_followups(created.id)

    assert len(followups) == 1
    assert followups[0].description == "Candidatura criada"
