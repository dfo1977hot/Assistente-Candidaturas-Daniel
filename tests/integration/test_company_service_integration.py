from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from acd.models.base import Base
from acd.services.company_service import CompanyService
import acd.database.database as db_module


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db_file = tmp_path / "integration_companies.db"
    engine = create_engine(f"sqlite:///{db_file}", echo=False, future=True)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(db_module, "SessionLocal", session_local)
    return session_local


def test_company_service_crud_and_duplicate_rule(isolated_db):
    service = CompanyService()

    created = service.create_company(
        name="Gamma",
        segment="Health",
        city="Campinas",
        state="SP",
        country="Brasil",
        company_size="Media",
        website="https://gamma.com",
        linkedin_url="https://linkedin.com/company/gamma",
        notes="primeiro cadastro",
    )
    assert created.id > 0

    with pytest.raises(ValueError):
        service.create_company(
            name="Gamma",
            segment="Health",
            city="Campinas",
            state="SP",
            country="Brasil",
            company_size="Media",
            website="https://gamma.com",
            linkedin_url="",
            notes="duplicada",
        )

    updated = service.update_company(
        created.id,
        name="Gamma Updated",
        segment="Health",
        city="Campinas",
        state="SP",
        country="Brasil",
        company_size="Grande",
        website="https://gamma.com",
        linkedin_url="",
        notes="atualizada",
    )
    assert updated is not None
    assert updated.name == "Gamma Updated"
    assert updated.company_size == "Grande"

    rows = service.search_companies("Gamma")
    assert len(rows) == 1

    assert service.delete_company(created.id) is True
    assert service.delete_company(created.id) is False
