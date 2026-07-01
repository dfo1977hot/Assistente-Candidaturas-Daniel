import os
import tempfile

import pytest

from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.services.company_service import CompanyService


@pytest.fixture
def temp_db(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-test-", dir=".")
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

    yield db_path

    Base.metadata.drop_all(bind=database_module.engine)


def test_create_and_list_company(temp_db):
    service = CompanyService(repository=CompanyRepository())
    company = service.create_company(name="Acme", city="São Paulo", website="https://acme.com")

    assert company.id is not None
    companies = service.list_companies()
    assert len(companies) == 1
    assert companies[0].name == "Acme"


def test_update_company(temp_db):
    service = CompanyService(repository=CompanyRepository())
    company = service.create_company(name="Acme", city="São Paulo", website="https://acme.com")

    updated = service.update_company(company.id, name="Acme LTDA", city="Campinas")

    assert updated is not None
    assert updated.name == "Acme LTDA"
    assert updated.city == "Campinas"


def test_delete_company(temp_db):
    service = CompanyService(repository=CompanyRepository())
    company = service.create_company(name="Acme", city="São Paulo", website="https://acme.com")

    assert service.delete_company(company.id) is True
    assert service.list_companies() == []


def test_list_company_returns_empty_when_none_exist(temp_db):
    service = CompanyService(repository=CompanyRepository())
    assert service.list_companies() == []
