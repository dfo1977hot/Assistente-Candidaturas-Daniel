from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from acd.models.base import Base
from acd.models.company import Company
from acd.infrastructure.repositories.company_repository import CompanyRepository
import acd.database.database as db_module


def _setup_temp_db(tmp_path: Path):
    db_file = tmp_path / "repo_companies.db"
    engine = create_engine(f"sqlite:///{db_file}", echo=False, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal


def test_company_repository_crud_search_and_sort(tmp_path, monkeypatch):
    session_local = _setup_temp_db(tmp_path)
    monkeypatch.setattr(db_module, "SessionLocal", session_local)

    repo = CompanyRepository()

    acme = repo.create(
        Company(
            name="Acme",
            segment="Tech",
            city="Sao Paulo",
            state="SP",
            country="Brasil",
            company_size="Media",
            website="https://acme.com",
            linkedin_url="https://linkedin.com/company/acme",
            notes="Cliente alvo",
        )
    )
    beta = repo.create(
        Company(
            name="Beta Corp",
            segment="Finance",
            city="Rio de Janeiro",
            state="RJ",
            country="Brasil",
            company_size="Grande",
            website="https://beta.com",
            linkedin_url="",
            notes="",
        )
    )

    assert repo.get_by_id(acme.id) is not None
    assert repo.count() == 2

    found = repo.search("Tech")
    assert len(found) == 1
    assert found[0].name == "Acme"

    sorted_rows = repo.get_all_sorted(by="city", descending=False)
    assert [item.city for item in sorted_rows] == ["Rio de Janeiro", "Sao Paulo"]

    assert repo.exists_by_name_and_website(name="Acme", website="https://acme.com") is True
    assert repo.exists_by_name_and_website(name="Acme", website="https://other.com") is False

    assert repo.delete(beta.id) is True
    assert repo.count() == 1
