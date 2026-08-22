import pytest

from acd.infrastructure.repositories.application_repository import ApplicationRepository
from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.infrastructure.repositories.curriculum_repository import CurriculumRepository
from acd.infrastructure.repositories.job_repository import JobRepository
from acd.services.application_service import ApplicationService
from acd.services.company_service import CompanyService
from acd.services.curriculum_service import CurriculumService
from acd.services.job_service import JobService


@pytest.fixture
def curriculum_setup(monkeypatch, tmp_path):
    temp_dir = tmp_path
    db_path = str(temp_dir / "test_acd.db")
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

    yield CurriculumService(repository=CurriculumRepository()), application.id

    Base.metadata.drop_all(bind=database_module.engine)


def test_curriculum_service_creates_and_activates_default(curriculum_setup):
    curriculum_service, _ = curriculum_setup

    created = curriculum_service.create_curriculum(
        name="Currículo Geral", version="v1.0", language="pt-BR"
    )
    assert created.id is not None
    activated = curriculum_service.activate_curriculum(created.id)
    assert activated is not None
    assert activated.is_default is True


def test_curriculum_service_duplicates_and_associates(curriculum_setup):
    curriculum_service, application_id = curriculum_setup

    base = curriculum_service.create_curriculum(
        name="Currículo Geral", version="v1.0", language="pt-BR"
    )
    duplicate = curriculum_service.duplicate_curriculum(base.id)

    assert duplicate.id is not None
    assert duplicate.version == "v1.1"

    associated = curriculum_service.associate_to_application(
        application_id=application_id, curriculum_id=duplicate.id
    )
    assert associated is not None
