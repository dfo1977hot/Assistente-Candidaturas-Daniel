from pathlib import Path

from sqlalchemy import create_engine

from acd.database.create_database import _ensure_companies_columns


def test_company_lookup_migration_is_idempotent(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'companies.db'}")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE companies (id INTEGER PRIMARY KEY, name TEXT NOT NULL, city TEXT NOT NULL)")
    _ensure_companies_columns(engine)
    _ensure_companies_columns(engine)
    with engine.connect() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(companies)")}
    assert {"legal_name", "tax_id", "registration_status", "address", "postal_code", "phone", "data_source", "source_reference", "data_retrieved_at"} <= columns
