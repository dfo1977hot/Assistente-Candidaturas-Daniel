from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from acd.models.base import Base
import acd.database.database as database_module


@pytest.fixture(scope="session")
def test_engine():
    """
    Cria um banco SQLite temporário para toda a sessão de testes.
    """

    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    engine = create_engine(
        f"sqlite:///{db_path}",
        future=True,
    )

    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()

    os.close(db_fd)

    os.remove(db_path)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Cria uma sessão isolada para cada teste.
    """

    SessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def override_database(db_session, test_engine, monkeypatch):
    """
    Faz toda a aplicação utilizar o banco temporário
    durante os testes.
    """

    monkeypatch.setattr(
        database_module,
        "engine",
        test_engine,
    )

    monkeypatch.setattr(
        database_module,
        "SessionLocal",
        lambda: db_session,
    )