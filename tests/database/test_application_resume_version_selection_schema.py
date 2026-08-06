from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

from acd.database import create_database as create_database_module
from acd.database.database import enable_sqlite_foreign_keys


def test_legacy_application_schema_evolves_idempotently_and_preserves_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "legacy.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE curricula (id INTEGER PRIMARY KEY);
        CREATE TABLE resume_versions (
            id INTEGER PRIMARY KEY,
            curriculum_id INTEGER NOT NULL REFERENCES curricula(id)
        );
        CREATE TABLE applications (
            id INTEGER PRIMARY KEY,
            curriculum_id INTEGER,
            curriculum_version TEXT
        );
        INSERT INTO curricula (id) VALUES (1);
        INSERT INTO applications (id, curriculum_id, curriculum_version) VALUES (7, 1, 'v1');
        """
    )
    connection.commit()
    connection.close()
    engine = create_engine(f"sqlite:///{database_path}")
    enable_sqlite_foreign_keys(engine)
    monkeypatch.setattr(create_database_module, "engine", engine)

    create_database_module._ensure_application_resume_version_selection()
    create_database_module._ensure_application_resume_version_selection()

    with engine.connect() as evolved:
        columns = {row[1]: row for row in evolved.exec_driver_sql("PRAGMA table_info(applications)")}
        foreign_keys = evolved.exec_driver_sql("PRAGMA foreign_key_list(applications)").fetchall()
        indexes = evolved.exec_driver_sql("PRAGMA index_list(applications)").fetchall()
        row = evolved.exec_driver_sql(
            "SELECT curriculum_id, curriculum_version, selected_resume_version_id FROM applications WHERE id = 7"
        ).one()
        assert evolved.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        assert columns["selected_resume_version_id"][2] == "INTEGER"
        assert columns["selected_resume_version_id"][3] == 0
        assert any(foreign_key[2:7] == ("resume_versions", "selected_resume_version_id", "id", "NO ACTION", "RESTRICT") for foreign_key in foreign_keys)
        assert [index[1] for index in indexes].count("ix_applications_selected_resume_version_id") == 1
        assert row == (1, "v1", None)
        assert evolved.exec_driver_sql("PRAGMA foreign_key_check").fetchall() == []


def test_selected_resume_version_is_restricted_until_the_selection_is_cleared(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'selection.db'}")
    enable_sqlite_foreign_keys(engine)
    create_database_module_engine = create_database_module.engine
    try:
        create_database_module.engine = engine
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE curricula (id INTEGER PRIMARY KEY)")
            connection.exec_driver_sql(
                "CREATE TABLE resume_versions ("
                "id INTEGER PRIMARY KEY, curriculum_id INTEGER NOT NULL REFERENCES curricula(id)"
                ")"
            )
            connection.exec_driver_sql(
                "CREATE TABLE applications ("
                "id INTEGER PRIMARY KEY, curriculum_id INTEGER, curriculum_version TEXT"
                ")"
            )
        create_database_module._ensure_application_resume_version_selection()
    finally:
        create_database_module.engine = create_database_module_engine

    with engine.begin() as connection:
        connection.exec_driver_sql("INSERT INTO curricula (id) VALUES (1)")
        connection.exec_driver_sql(
            "INSERT INTO resume_versions (id, curriculum_id) VALUES (2, 1)"
        )
        connection.exec_driver_sql(
            "INSERT INTO applications (id, curriculum_id, selected_resume_version_id) "
            "VALUES (3, 1, 2)"
        )
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.exec_driver_sql("DELETE FROM resume_versions WHERE id = 2")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE applications SET selected_resume_version_id = NULL WHERE id = 3"
        )
        connection.exec_driver_sql("DELETE FROM resume_versions WHERE id = 2")
