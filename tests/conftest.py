from __future__ import annotations

import os
import tempfile

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import acd.database.create_database as create_database_module
import acd.database.database as database_module
from acd.database.database import enable_sqlite_foreign_keys
from acd.database.model_registry import load_models
from acd.models.base import Base

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.company",
]


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def cleanup_qt_widgets(qapp: QApplication):
    """Dispose test-created top-level widgets before the next Qt test starts."""

    yield

    for widget in qapp.topLevelWidgets():
        widget.close()
        widget.deleteLater()

    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


@pytest.fixture(scope="session")
def test_engine():
    load_models()
    """Cria um banco SQLite temporário para toda a sessão de testes."""

    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    engine = create_engine(
        f"sqlite:///{db_path}",
        future=True,
    )
    enable_sqlite_foreign_keys(engine)

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
    """Cria uma sessão isolada para cada teste."""

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
        if session.is_active:
            session.rollback()

        session.close()


@pytest.fixture(autouse=True)
def override_database(db_session, test_engine, monkeypatch):
    """Faz toda a aplicação utilizar o banco temporário durante os testes."""

    monkeypatch.setattr(
        database_module,
        "engine",
        test_engine,
    )
    monkeypatch.setattr(
        create_database_module,
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

    try:
        yield
    finally:
        database_module.engine.dispose()
