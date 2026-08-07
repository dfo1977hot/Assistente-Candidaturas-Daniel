"""Stable budgets and resource-count checks for critical desktop paths."""

from __future__ import annotations

import gc
import json
import logging
import os
from pathlib import Path
import statistics
import subprocess
import sys
import threading
import time
import tracemalloc
from types import SimpleNamespace

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from acd.application.query_ports import VacancyQueryDTO
from acd.application.structured_resume_generation import StructuredResumeProviderRequest
from acd.application.structured_resume_snapshot import StructuredResumeSnapshotCodec
import acd.database.database as database_module
from acd.database.database import enable_sqlite_foreign_keys
from acd.database.database_bootstrap import DatabaseBootstrap
from acd.domain.entities.application import Application
from acd.domain.entities.job import Job
from acd.infrastructure.ai.openai_structured_resume_provider import (
    OpenAIStructuredResumeGenerationProvider,
    OpenAIStructuredResumeResponse,
    OpenAIStructuredResumeSettings,
)
from acd.infrastructure.database.sqlite_lifecycle import SQLiteDatabaseLifecycle
from acd.infrastructure.release.plugin_loader import PluginLoader
from acd.infrastructure.repositories.application_repository import ApplicationRepository
from acd.models.base import Base
from acd.models.company import Company
from acd.presentation.long_running_task_executor import LongRunningTaskExecutor
from acd.presentation.pages.application_page import ApplicationPage
from acd.ui.sidebar import Sidebar

ROOT = Path(__file__).resolve().parents[2]


def _cold_import_ms(module: str, working_directory: Path) -> float:
    code = (
        "import importlib,time;"
        "start=time.perf_counter();"
        f"importlib.import_module({module!r});"
        "print((time.perf_counter()-start)*1000)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=working_directory,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        check=True,
    )
    return float(completed.stdout.strip())


@pytest.mark.parametrize(("module", "budget_ms"), [("acd", 2000.0), ("acd.desktop", 10000.0)])
def test_cold_import_is_bounded_and_side_effect_free(module, budget_ms, tmp_path) -> None:
    before = set(tmp_path.iterdir())
    samples = [_cold_import_ms(module, tmp_path) for _ in range(3)]
    assert statistics.median(samples) < budget_ms
    assert set(tmp_path.iterdir()) == before


def test_bootstrap_new_and_existing_database_have_tolerant_budgets(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'performance.db'}")
    try:
        start = time.perf_counter()
        first = DatabaseBootstrap().initialize(engine)
        new_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        existing = DatabaseBootstrap().initialize(engine)
        existing_ms = (time.perf_counter() - start) * 1000
    finally:
        engine.dispose()
    assert len(first.physical_tables) == len(existing.physical_tables) == 92
    assert new_ms < 5000
    assert existing_ms < 3000


def test_sidebar_and_application_page_creation_are_bounded(qtbot) -> None:
    start = time.perf_counter()
    sidebar = Sidebar()
    sidebar_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    page = ApplicationPage()
    page_ms = (time.perf_counter() - start) * 1000
    qtbot.addWidget(sidebar)
    qtbot.addWidget(page)
    assert sidebar_ms < 500
    assert page_ms < 1000


def test_executor_has_capacity_one_and_rejects_without_backlog(qtbot) -> None:
    executor = LongRunningTaskExecutor()
    started = threading.Event()
    release = threading.Event()

    executor.execute(lambda: started.set() or release.wait())
    qtbot.waitUntil(started.is_set)
    assert (executor.queue_capacity, executor.queue_depth) == (1, 1)
    with pytest.raises(RuntimeError, match="already running"):
        executor.execute(lambda: None)
    with qtbot.waitSignal(executor.finished):
        release.set()
    assert executor.queue_depth == 0


def test_event_loop_remains_responsive_and_cancel_latency_is_bounded(qtbot) -> None:
    executor = LongRunningTaskExecutor()
    started = threading.Event()
    release = threading.Event()
    executor.execute(lambda: started.set() or release.wait())
    qtbot.waitUntil(started.is_set)
    QApplication.processEvents()
    start = time.perf_counter()
    assert executor.cancel()
    request_ms = (time.perf_counter() - start) * 1000
    with qtbot.waitSignal(executor.finished):
        release.set()
    assert request_ms < 250


def test_application_list_query_is_one_statement_without_n_plus_one(tmp_path, monkeypatch) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'queries.db'}")
    enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine)
    monkeypatch.setattr(database_module, "SessionLocal", local_session)
    with local_session() as session:
        company = Company(name="Synthetic", city="Synthetic city")
        session.add(company)
        session.flush()
        job = Job(company_id=company.id, title="Synthetic role")
        session.add(job)
        session.flush()
        session.add_all(
            [
                Application(company_id=company.id, job_id=job.id, notes=f"item-{i}")
                for i in range(50)
            ]
        )
        session.commit()
    statements: list[str] = []

    def record_statement(*args) -> None:
        statements.append(str(args[2]))

    event.listen(engine, "before_cursor_execute", record_statement)
    try:
        applications = ApplicationRepository().get_all()
        assert len(applications) == 50
        assert applications[0].company.name == "Synthetic"
        assert applications[0].job.title == "Synthetic role"
        assert len(statements) == 1
    finally:
        event.remove(engine, "before_cursor_execute", record_statement)
        engine.dispose()


def test_repeated_widget_and_logging_cycles_leave_no_owned_resources(qtbot) -> None:
    baseline_handlers = tuple(logging.getLogger().handlers)
    tracemalloc.start()
    before = tracemalloc.take_snapshot()
    for _ in range(10):
        page = ApplicationPage()
        page.close()
        page.deleteLater()
        QApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        QApplication.processEvents()
    gc.collect()
    after = tracemalloc.take_snapshot()
    growth = sum(stat.size_diff for stat in after.compare_to(before, "filename"))
    tracemalloc.stop()
    assert not [thread for thread in threading.enumerate() if thread.name.startswith("QThread")]
    assert tuple(logging.getLogger().handlers) == baseline_handlers
    assert growth < 8 * 1024 * 1024


def test_temporary_backup_and_restore_are_bounded(tmp_path) -> None:
    source = tmp_path / "source.db"
    engine = create_engine(f"sqlite:///{source}")
    DatabaseBootstrap().initialize(engine)
    engine.dispose()
    lifecycle = SQLiteDatabaseLifecycle()
    backup = tmp_path / "backup.db"
    restored = tmp_path / "restored.db"
    start = time.perf_counter()
    created = lifecycle.create_backup(source, backup)
    backup_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    result = lifecycle.restore_backup(backup, restored, expected_sha256=created.sha256)
    restore_ms = (time.perf_counter() - start) * 1000
    assert result.table_count == created.table_count == 92
    assert backup_ms < 10_000
    assert restore_ms < 10_000


def test_synthetic_plugin_discovery_load_and_shutdown_are_bounded(tmp_path) -> None:
    root = tmp_path / "plugins"
    plugin = root / "synthetic_plugin"
    plugin.mkdir(parents=True)
    (plugin / "plugin.json").write_text(
        json.dumps(
            {
                "name": "synthetic_plugin",
                "version": "1.0.0",
                "author": "test",
                "description": "performance fixture",
                "entry_point": "main:SyntheticPlugin",
                "min_app_version": "0.1.0",
            }
        ),
        encoding="utf-8",
    )
    (plugin / "main.py").write_text(
        "from acd.infrastructure.release.plugin_loader import PluginInterface\n"
        "class SyntheticPlugin(PluginInterface):\n"
        "    def get_metadata(self): return None\n"
        "    def initialize(self, context): return True\n",
        encoding="utf-8",
    )
    loader = PluginLoader([str(root)], allowed_plugins=frozenset({"synthetic_plugin"}))
    start = time.perf_counter()
    assert loader.discover_plugins() == ["synthetic_plugin"]
    assert loader.load_plugin("synthetic_plugin")
    loader.shutdown_all()
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert not loader.loaded_plugins
    assert elapsed_ms < 2_000


def test_fake_openai_adapter_request_cycle_is_bounded_and_closed() -> None:
    payload = {
        "schema_version": 1,
        "identity": {"full_name": "Synthetic", "professional_title": "Engineer", "location": None},
        "contact": {
            "email": None,
            "phone": None,
            "linkedin": None,
            "portfolio": None,
            "website": None,
        },
        "summary": "Synthetic profile",
        "skills": ["Python"],
        "experiences": [],
        "education": [],
        "certifications": [],
        "courses": [],
        "languages": [],
        "projects": [],
        "additional_sections": [],
    }
    snapshot = StructuredResumeSnapshotCodec().from_payload(payload)
    request = StructuredResumeProviderRequest(
        snapshot,
        VacancyQueryDTO(1, "Engineer", 1, "Remote", "Python", ("Python",)),
        ("Keep facts",),
    )
    parsed = OpenAIStructuredResumeResponse.model_validate(
        {"resume": payload, "explanation": "Synthetic response"}
    )

    class FakeResponses:
        def parse(self, **_kwargs):
            return SimpleNamespace(output_parsed=parsed, _request_id="synthetic")

    class FakeClient:
        def __init__(self) -> None:
            self.responses = FakeResponses()
            self.closed = False

        def close(self) -> None:
            self.closed = True

    client = FakeClient()
    provider = OpenAIStructuredResumeGenerationProvider(
        OpenAIStructuredResumeSettings("test-key", "gpt-test"), client=client
    )
    start = time.perf_counter()
    result = provider.generate_structured_resume(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    provider.close()
    assert result.structured_resume is not None
    assert client.closed
    assert elapsed_ms < 2_000
