from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from acd.models.base import Base
from acd.models.company import Company


def _session_local(tmp_path: Path):
    db_file = tmp_path / "db_companies.db"
    engine = create_engine(f"sqlite:///{db_file}", echo=False, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False), engine


def test_company_table_has_required_columns(tmp_path):
    _, engine = _session_local(tmp_path)
    columns = {c["name"] for c in inspect(engine).get_columns("companies")}

    expected = {
        "id",
        "name",
        "segment",
        "city",
        "state",
        "country",
        "company_size",
        "website",
        "linkedin_url",
        "notes",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns)


def test_company_data_persists_between_sessions(tmp_path):
    SessionLocal, _ = _session_local(tmp_path)

    with SessionLocal() as session:
        session.add(
            Company(
                name="Persist Inc",
                segment="Services",
                city="Curitiba",
                state="PR",
                country="Brasil",
                company_size="Pequena",
                website="https://persist.com",
                linkedin_url="",
                notes="check persistence",
            )
        )
        session.commit()

    with SessionLocal() as session:
        row = session.query(Company).filter(Company.name == "Persist Inc").first()
        assert row is not None
        assert row.city == "Curitiba"
