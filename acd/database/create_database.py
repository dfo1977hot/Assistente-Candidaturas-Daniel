"""Database initialization."""

# Importa todos os modelos ORM para registrá-los no Base.metadata
import acd.database.model_registry  # noqa: F401

from acd.database.database import engine
from acd.models.base import Base


def create_database() -> None:
    """Create database schema if it does not exist."""
    Base.metadata.create_all(engine)
    _ensure_companies_columns()


def _ensure_companies_columns() -> None:
    required_columns = {
        "segment": "TEXT NOT NULL DEFAULT ''",
        "state": "TEXT NOT NULL DEFAULT ''",
        "country": "TEXT NOT NULL DEFAULT ''",
        "company_size": "TEXT NOT NULL DEFAULT ''",
        "linkedin_url": "TEXT DEFAULT ''",
    }

    with engine.begin() as connection:
        existing_rows = connection.exec_driver_sql(
            "PRAGMA table_info(companies)"
        ).fetchall()

        existing_columns = {row[1] for row in existing_rows}

        for column_name, column_type in required_columns.items():
            if column_name in existing_columns:
                continue

            connection.exec_driver_sql(
                f"ALTER TABLE companies "
                f"ADD COLUMN {column_name} {column_type}"
            )


if __name__ == "__main__":
    create_database()
    print("Banco criado com sucesso.")