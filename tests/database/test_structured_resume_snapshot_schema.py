"""SQLite schema evolution tests for versioned structured resume snapshots."""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest
from sqlalchemy import create_engine

from acd.database import create_database as create_database_module
from acd.database.database import enable_sqlite_foreign_keys


def test_legacy_resume_tables_evolve_idempotently_preserving_existing_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "legacy.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE curricula (id INTEGER PRIMARY KEY, description TEXT NOT NULL);
        CREATE TABLE resume_versions (
            id INTEGER PRIMARY KEY,
            curriculum_id INTEGER NOT NULL REFERENCES curricula(id),
            content TEXT NOT NULL
        );
        INSERT INTO curricula (id, description) VALUES (1, 'legacy curriculum');
        INSERT INTO resume_versions (id, curriculum_id, content) VALUES (2, 1, 'legacy version');
        """
    )
    connection.commit()
    connection.close()
    engine = create_engine(f"sqlite:///{database_path}")
    enable_sqlite_foreign_keys(engine)
    monkeypatch.setattr(create_database_module, "engine", engine)

    backup = create_database_module._ensure_structured_resume_snapshot_columns()
    assert backup is not None and backup.exists()
    assert create_database_module._ensure_structured_resume_snapshot_columns() is None

    with engine.connect() as evolved:
        curricula = {row[1]: row for row in evolved.exec_driver_sql("PRAGMA table_info(curricula)")}
        versions = {row[1]: row for row in evolved.exec_driver_sql("PRAGMA table_info(resume_versions)")}
        assert curricula["structured_content_json"][2] == "TEXT"
        assert versions["structured_content_json"][2] == "TEXT"
        assert curricula["structured_content_json"][3:5] == (0, None)
        assert versions["structured_content_json"][3:5] == (0, None)
        assert evolved.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        assert evolved.exec_driver_sql("PRAGMA foreign_key_check").fetchall() == []
        assert evolved.exec_driver_sql(
            "SELECT description, structured_content_json FROM curricula WHERE id = 1"
        ).one() == ("legacy curriculum", None)
        assert evolved.exec_driver_sql(
            "SELECT content, structured_content_json FROM resume_versions WHERE id = 2"
        ).one() == ("legacy version", None)
