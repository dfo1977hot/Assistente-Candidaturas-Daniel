"""Tests for the official SQLite foreign-key connection policy."""

from __future__ import annotations

from sqlalchemy import create_engine, text

from acd.database.database import enable_sqlite_foreign_keys, engine


def test_official_engine_enables_foreign_keys_for_each_connection() -> None:
    """The official engine configures referential enforcement centrally."""
    with engine.connect() as first_connection:
        assert first_connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    with engine.connect() as second_connection:
        assert second_connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1


def test_foreign_key_listener_registration_is_idempotent() -> None:
    """Registering the SQLite listener twice must not duplicate the event."""
    isolated_engine = create_engine("sqlite:///:memory:")
    try:
        enable_sqlite_foreign_keys(isolated_engine)
        enable_sqlite_foreign_keys(isolated_engine)

        with isolated_engine.connect() as connection:
            assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    finally:
        isolated_engine.dispose()
