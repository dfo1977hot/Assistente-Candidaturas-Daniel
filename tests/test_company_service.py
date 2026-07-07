import os
import tempfile

import pytest

from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.services.company_service import CompanyService


@pytest.fixture
def service_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-service-", dir=".")
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

    yield CompanyService(repository=CompanyRepository())

    Base.metadata.drop_all(bind=database_module.engine)


def test_service_creates_and_searches_company(service_setup):
    created = service_setup.create_company(
        name="Acme", city="São Paulo", website="https://acme.com"
    )

    assert created.id is not None
    assert service_setup.count_companies() == 1
    assert service_setup.search_companies("Acme")[0].name == "Acme"


def test_service_updates_and_deletes_company(service_setup):
    created = service_setup.create_company(name="Acme", city="São Paulo")
    updated = service_setup.update_company(created.id, name="Acme LTDA", city="Campinas")

    assert updated is not None
    assert updated.name == "Acme LTDA"
    assert service_setup.delete_company(created.id) is True
    assert service_setup.count_companies() == 0
