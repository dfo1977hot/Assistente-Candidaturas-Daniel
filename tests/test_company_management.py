import os
import tempfile

import pytest

from acd.application.company.create_company import create_company
from acd.application.company.update_company import update_company
from acd.application.company.delete_company import delete_company
from acd.application.company.list_company import list_companies
from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.models.company import Company


@pytest.fixture
def temp_db(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-test-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd.db")
    monkeypatch.setattr(
        "acd.infrastructure.repositories.company_repository.DATABASE_FILE",
        db_path,
    )
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
    repo = CompanyRepository()
    company = create_company(repo, name="Acme", city="São Paulo", website="https://acme.com")

    assert company.id is not None
    companies = list_companies(repo)
    assert len(companies) == 1
    assert companies[0].name == "Acme"


def test_update_company(temp_db):
    repo = CompanyRepository()
    company = create_company(repo, name="Acme", city="São Paulo", website="https://acme.com")

    updated = update_company(repo, company.id, name="Acme LTDA", city="Campinas")

    assert updated is not None
    assert updated.name == "Acme LTDA"
    assert updated.city == "Campinas"


def test_delete_company(temp_db):
    repo = CompanyRepository()
    company = create_company(repo, name="Acme", city="São Paulo", website="https://acme.com")

    assert delete_company(repo, company.id) is True
    assert list_companies(repo) == []


def test_list_company_returns_empty_when_none_exist(temp_db):
    repo = CompanyRepository()
    assert list_companies(repo) == []
