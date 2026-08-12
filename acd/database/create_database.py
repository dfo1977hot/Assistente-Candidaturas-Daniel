"""Database initialization."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from pathlib import Path
import shutil

from sqlalchemy import Engine

from acd.database.database import engine
from acd.database.database_bootstrap import DatabaseBootstrap
from acd.database.local_state import prepare_database_directory

# Importa todos os modelos ORM para registrá-los no Base.metadata

logger = logging.getLogger(__name__)


def create_database(target_engine: Engine | None = None) -> None:
    """Create the database schema if it does not already exist."""
    selected_engine = target_engine or engine
    database_name = selected_engine.url.database
    if database_name and database_name != ":memory:":
        prepare_database_directory(Path(database_name).resolve())
    DatabaseBootstrap().initialize(selected_engine)
    _ensure_companies_columns(selected_engine)
    _ensure_application_resume_version_selection(selected_engine)
    _ensure_structured_resume_snapshot_columns(selected_engine)
    _ensure_curriculum_document_columns(selected_engine)
    _ensure_job_application_url_column(selected_engine)
    _ensure_job_recruiter_email_column(selected_engine)
    _ensure_cover_letter_columns(selected_engine)


def _ensure_companies_columns(target_engine: Engine | None = None) -> None:
    """Ensure the companies table contains all required columns."""

    required_columns = {
        "segment": "TEXT NOT NULL DEFAULT ''",
        "state": "TEXT NOT NULL DEFAULT ''",
        "country": "TEXT NOT NULL DEFAULT ''",
        "company_size": "TEXT NOT NULL DEFAULT ''",
        "linkedin_url": "TEXT DEFAULT ''",
        "legal_name": "TEXT NOT NULL DEFAULT ''",
        "tax_id": "TEXT NOT NULL DEFAULT ''",
        "registration_status": "TEXT NOT NULL DEFAULT ''",
        "address": "TEXT NOT NULL DEFAULT ''",
        "postal_code": "TEXT NOT NULL DEFAULT ''",
        "phone": "TEXT NOT NULL DEFAULT ''",
        "data_source": "TEXT NOT NULL DEFAULT ''",
        "source_reference": "TEXT NOT NULL DEFAULT ''",
        "data_retrieved_at": "DATETIME",
    }

    selected_engine = target_engine or engine
    with selected_engine.begin() as connection:
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


def _ensure_application_resume_version_selection(target_engine: Engine | None = None) -> None:
    """Add the nullable selected resume version column to legacy databases."""

    selected_engine = target_engine or engine
    with selected_engine.begin() as connection:
        existing_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(applications)").fetchall()
        }
        if "selected_resume_version_id" not in existing_columns:
            connection.exec_driver_sql(
                "ALTER TABLE applications "
                "ADD COLUMN selected_resume_version_id INTEGER "
                "REFERENCES resume_versions(id) ON DELETE RESTRICT"
            )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_applications_selected_resume_version_id "
            "ON applications(selected_resume_version_id)"
        )


def _ensure_structured_resume_snapshot_columns(target_engine: Engine | None = None) -> Path | None:
    """Add nullable structured snapshot columns to existing SQLite databases."""

    required_columns = {
        "curricula": "structured_content_json",
        "resume_versions": "structured_content_json",
    }
    selected_engine = target_engine or engine
    with selected_engine.connect() as connection:
        missing = [
            (table, column)
            for table, column in required_columns.items()
            if column
            not in {
                row[1]
                for row in connection.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            }
        ]
    if not missing:
        return None

    backup_path = _backup_database_before_schema_evolution(selected_engine)
    with selected_engine.begin() as connection:
        for table, column in missing:
            connection.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
    return backup_path


def _backup_database_before_schema_evolution(target_engine: Engine | None = None) -> Path | None:
    """Create a timestamped copy before changing a file-backed SQLite schema."""

    selected_engine = target_engine or engine
    database_name = selected_engine.url.database
    if database_name is None or database_name == ":memory:":
        return None
    database_path = Path(database_name)
    if not database_path.exists():
        return None
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = database_path.with_name(f"{database_path.stem}.pre-structured-resume-{timestamp}.bak")
    shutil.copy2(database_path, backup_path)
    logger.info("Created database backup before structured resume schema evolution: %s", backup_path)
    return backup_path


def _ensure_curriculum_document_columns(
    target_engine: Engine | None = None,
) -> Path | None:
    """Add nullable curriculum document metadata columns idempotently."""

    required_columns = {
        "file_original_name": "TEXT",
        "file_relative_path": "TEXT",
        "file_extension": "TEXT",
        "file_mime_type": "TEXT",
        "file_size_bytes": "INTEGER",
        "file_sha256": "TEXT",
        "file_attached_at": "DATETIME",
    }
    selected_engine = target_engine or engine
    with selected_engine.connect() as connection:
        existing = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(curricula)"
            ).fetchall()
        }
    missing = [
        (column_name, column_type)
        for column_name, column_type in required_columns.items()
        if column_name not in existing
    ]
    if not missing:
        return None

    backup_path = _backup_database_before_curriculum_document_evolution(
        selected_engine
    )
    with selected_engine.begin() as connection:
        for column_name, column_type in missing:
            connection.exec_driver_sql(
                f"ALTER TABLE curricula ADD COLUMN {column_name} {column_type}"
            )
    return backup_path


def _backup_database_before_curriculum_document_evolution(
    target_engine: Engine | None = None,
) -> Path | None:
    """Back up a file-backed SQLite database before the H.1-D migration."""

    selected_engine = target_engine or engine
    database_name = selected_engine.url.database
    if database_name is None or database_name == ":memory:":
        return None
    database_path = Path(database_name)
    if not database_path.exists():
        return None
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = database_path.with_name(
        f"{database_path.stem}.pre-curriculum-documents-{timestamp}.bak"
    )
    shutil.copy2(database_path, backup_path)
    logger.info(
        "Created database backup before curriculum document schema evolution: %s",
        backup_path,
    )
    return backup_path


def _ensure_job_application_url_column(
    target_engine: Engine | None = None,
) -> None:
    """Add the external application URL column to legacy job tables."""

    selected_engine = target_engine or engine
    with selected_engine.begin() as connection:
        existing_columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(jobs)"
            ).fetchall()
        }
        if "application_url" not in existing_columns:
            connection.exec_driver_sql(
                "ALTER TABLE jobs ADD COLUMN application_url TEXT NOT NULL DEFAULT ''"
            )



def _ensure_job_recruiter_email_column(
    target_engine: Engine | None = None,
) -> None:
    """Add recruiter/RH e-mail to existing job tables."""

    selected_engine = target_engine or engine
    with selected_engine.begin() as connection:
        existing_columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(jobs)"
            ).fetchall()
        }
        if "recruiter_email" not in existing_columns:
            connection.exec_driver_sql(
                "ALTER TABLE jobs "
                "ADD COLUMN recruiter_email TEXT NOT NULL DEFAULT ''"
            )


def _ensure_cover_letter_columns(
    target_engine: Engine | None = None,
) -> None:
    """Evolve legacy cover_letter_versions for the Cartas workspace."""

    required_columns = {
        "job_id": "INTEGER REFERENCES jobs(id)",
        "application_id": "INTEGER REFERENCES applications(id)",
        "letter_type": "TEXT NOT NULL DEFAULT 'Carta de Apresentação'",
        "language": "TEXT NOT NULL DEFAULT 'Português'",
        "tone": "TEXT NOT NULL DEFAULT 'Profissional'",
        "length": "TEXT NOT NULL DEFAULT 'Média'",
        "subject": "TEXT NOT NULL DEFAULT ''",
        "status": "TEXT NOT NULL DEFAULT 'Rascunho'",
        "notes": "TEXT NOT NULL DEFAULT ''",
        "updated_at": "DATETIME",
    }
    selected_engine = target_engine or engine
    with selected_engine.begin() as connection:
        existing = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(cover_letter_versions)"
            ).fetchall()
        }
        for column_name, column_type in required_columns.items():
            if column_name not in existing:
                connection.exec_driver_sql(
                    f"ALTER TABLE cover_letter_versions "
                    f"ADD COLUMN {column_name} {column_type}"
                )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_cover_letter_versions_job_id "
            "ON cover_letter_versions(job_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_cover_letter_versions_application_id "
            "ON cover_letter_versions(application_id)"
        )


if __name__ == "__main__":
    create_database()
    logger.info("Database schema created successfully.")
