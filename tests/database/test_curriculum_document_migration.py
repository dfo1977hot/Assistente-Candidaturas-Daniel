from pathlib import Path

from sqlalchemy import create_engine

from acd.database.create_database import _ensure_curriculum_document_columns

EXPECTED_COLUMNS = {
    "file_original_name",
    "file_relative_path",
    "file_extension",
    "file_mime_type",
    "file_size_bytes",
    "file_sha256",
    "file_attached_at",
}


def test_curriculum_document_migration_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "acd.db"
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE curricula (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
        connection.exec_driver_sql(
            "INSERT INTO curricula (id, name) VALUES (1, 'Currículo principal')"
        )

    first_backup = _ensure_curriculum_document_columns(engine)
    second_backup = _ensure_curriculum_document_columns(engine)

    with engine.connect() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(curricula)"
            ).fetchall()
        }
        row = connection.exec_driver_sql(
            "SELECT id, name FROM curricula WHERE id = 1"
        ).one()

    assert EXPECTED_COLUMNS <= columns
    assert row == (1, "Currículo principal")
    assert first_backup is not None and first_backup.exists()
    assert second_backup is None
