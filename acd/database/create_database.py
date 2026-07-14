"""Database initialization."""

from __future__ import annotations

import logging

from acd.database.database import engine

# Importa todos os modelos ORM para registrá-los no Base.metadata
import acd.database.model_registry  # noqa: F401
from acd.models.base import Base

logger = logging.getLogger(__name__)


def create_database() -> None:
    """Create the database schema if it does not already exist."""
    Base.metadata.create_all(engine)
    _ensure_companies_columns()


def _ensure_companies_columns() -> None:
    """Ensure the companies table contains all required columns."""

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
    logger.info("Database schema created successfully.")