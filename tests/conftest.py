from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import acd.database.database as database_module

# Garante o registro de todos os modelos ORM antes do create_all().
import acd.database.model_registry  # noqa: F401
from acd.models.base import Base

pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.company",
]


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

    Base.metadata.create_all(bind=engine)

    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

        os.close(db_fd)

        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Cria uma sessão isolada para cada teste.

    Antes de cada teste o banco é recriado para garantir
    isolamento completo entre os casos de teste.
    """

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    SessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def override_database(db_session, test_engine, monkeypatch):
    """
    Faz toda a aplicação utilizar o banco temporário durante os testes.
    """

    monkeypatch.setattr(
        database_module,
        "engine",
        test_engine,
    )

    monkeypatch.setattr(
        database_module,
        "SessionLocal",
        sessionmaker(
            bind=test_engine,
            autoflush=False,
            autocommit=False,
            future=True,
        ),
    )

    yield