from __future__ import annotations

import os
import tempfile

import pytest

from acd.database import database as database_module
from acd.database.local_state import ensure_non_productive_database_path
from acd.models.base import Base


@pytest.fixture(scope="function")
def db_engine(monkeypatch):
    """
    Cria um banco SQLite temporário para cada teste.
    """

    temp_dir = tempfile.mkdtemp(prefix="acd-test-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd.db")
    ensure_non_productive_database_path(db_path)

    monkeypatch.setattr(
        "acd.database.database.DATABASE_URL",
        f"sqlite:///{db_path}",
    )

    database_module.engine.dispose()

    database_module.engine = database_module.create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        future=True,
    )

    database_module.SessionLocal = database_module.sessionmaker(
        bind=database_module.engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    yield database_module.engine

    Base.metadata.drop_all(bind=database_module.engine)
    database_module.engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Sessão SQLAlchemy isolada.
    """

    session = database_module.SessionLocal()

    try:
        yield session
    finally:
        session.close()