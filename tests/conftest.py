from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import acd.database.database as database_module

# Importa o registro centralizado dos modelos ORM.
# Este import não é utilizado diretamente, mas garante que todos os
# modelos sejam registrados no Base.metadata antes do create_all().
import acd.database.model_registry  # noqa: F401

from acd.models.base import Base


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

    print("\n=== TABELAS REGISTRADAS ===")
    print(sorted(Base.metadata.tables.keys()))

    for table in Base.metadata.tables.values():
        for fk in table.foreign_keys:
            print(f"{table.name}: {fk.target_fullname}")

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