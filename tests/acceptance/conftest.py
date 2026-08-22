from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import QWidget
import pytest
from shiboken6 import isValid
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from acd.core.router import Router
from acd.database import database as database_module
from acd.database.create_database import create_database
from acd.database.database import enable_sqlite_foreign_keys
from acd.database.local_state import ensure_non_productive_database_path, sqlite_url
from acd.infrastructure.database.sqlite_lifecycle import SQLiteDatabaseLifecycle
from acd.infrastructure.repositories.analytics_repository import AnalyticsRepository
from acd.infrastructure.repositories.curriculum_repository import CurriculumRepository
from acd.presentation.pages.application_page import ApplicationPage
from acd.presentation.pages.base_page import BasePage
from acd.presentation.pages.company_page import CompanyPage
from acd.presentation.pages.curriculum_page import CurriculumPage
from acd.presentation.pages.interview_page import InterviewPage
from acd.presentation.pages.job_page import JobPage
from acd.services.analytics_service import AnalyticsService
from acd.services.application_service import ApplicationService
from acd.services.company_service import CompanyService
from acd.services.curriculum_service import CurriculumService
from acd.services.interview_service import InterviewService
from acd.services.job_service import JobService
from acd.services.settings_service import SettingsService
from acd.ui.dashboard import Dashboard
from acd.ui.main_window import MainWindow
from acd.ui.sidebar import Sidebar


@dataclass(slots=True)
class AcceptanceRuntime:
    workspace: Path
    database_path: Path
    backup_dir: Path
    exports_dir: Path
    attachments_dir: Path
    logs_dir: Path
    evidence_dir: Path
    engine: Engine
    window: MainWindow
    dashboard: Dashboard
    company_page: CompanyPage
    job_page: JobPage
    application_page: ApplicationPage
    interview_page: InterviewPage
    curriculum_page: CurriculumPage
    company_service: CompanyService
    job_service: JobService
    application_service: ApplicationService
    interview_service: InterviewService
    curriculum_service: CurriculumService
    lifecycle: SQLiteDatabaseLifecycle

    def close(self) -> None:
        if isValid(self.window):
            self.window.close()
        self.engine.dispose()


def _select_combo_data(combo: object, value: object) -> None:
    index = combo.findData(value)  # type: ignore[attr-defined]
    if index < 0:
        raise AssertionError(f"Combo value not found: {value!r}")
    combo.setCurrentIndex(index)  # type: ignore[attr-defined]


def build_acceptance_runtime(
    monkeypatch: pytest.MonkeyPatch,
    qtbot,
    workspace: Path,
    *,
    database_path: Path | None = None,
) -> AcceptanceRuntime:
    workspace.mkdir(parents=True, exist_ok=True)
    database_root = workspace / "database"
    backup_dir = workspace / "backups"
    exports_dir = workspace / "exports"
    attachments_dir = workspace / "attachments"
    logs_dir = workspace / "logs"
    evidence_dir = workspace / "evidence"
    for directory in (
        database_root,
        backup_dir,
        exports_dir,
        attachments_dir,
        logs_dir,
        evidence_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    resolved_database_path = ensure_non_productive_database_path(
        database_path or (database_root / "acd-acceptance.db")
    )
    engine = create_engine(sqlite_url(resolved_database_path), future=True)
    enable_sqlite_foreign_keys(engine)
    create_database(engine)

    monkeypatch.setattr(
        database_module,
        "engine",
        engine,
    )
    monkeypatch.setattr(
        database_module,
        "SessionLocal",
        sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            future=True,
        ),
    )

    company_service = CompanyService()
    job_service = JobService()
    application_service = ApplicationService()
    interview_service = InterviewService()
    curriculum_service = object.__new__(CurriculumService)
    curriculum_service.repository = CurriculumRepository()
    curriculum_service.storage_root = attachments_dir / "curriculos"
    curriculum_service.storage_root.mkdir(parents=True, exist_ok=True)

    dashboard = Dashboard(AnalyticsService(AnalyticsRepository()))
    company_page = CompanyPage(company_service)
    job_page = JobPage(job_service, company_service)
    application_page = ApplicationPage(
        application_service=application_service,
        company_service=company_service,
        job_service=job_service,
    )
    interview_page = InterviewPage(interview_service, application_service)
    curriculum_page = CurriculumPage(curriculum_service)

    pages: dict[str, QWidget] = {
        "dashboard": dashboard,
        "companies": company_page,
        "jobs": job_page,
        "applications": application_page,
        "interviews": interview_page,
        "curricula": curriculum_page,
        "workflows": BasePage("Workflows"),
        "analytics": BasePage("Analytics"),
        "career": BasePage("Career"),
        "assistant": BasePage("Assistant"),
        "agent_console": BasePage("Agentes"),
        "cover_letters": BasePage("Cartas"),
        "crm": BasePage("CRM"),
        "candidate_profile": BasePage("Perfil do Candidato"),
        "settings": BasePage("Configuracoes"),
    }
    settings_service = SettingsService(workspace / "settings.json")
    window = MainWindow(
        sidebar=Sidebar(),
        router=Router(),
        pages=pages,
        settings_service=settings_service,
    )
    qtbot.addWidget(window)

    lifecycle = SQLiteDatabaseLifecycle()
    return AcceptanceRuntime(
        workspace=workspace,
        database_path=resolved_database_path,
        backup_dir=backup_dir,
        exports_dir=exports_dir,
        attachments_dir=attachments_dir,
        logs_dir=logs_dir,
        evidence_dir=evidence_dir,
        engine=engine,
        window=window,
        dashboard=dashboard,
        company_page=company_page,
        job_page=job_page,
        application_page=application_page,
        interview_page=interview_page,
        curriculum_page=curriculum_page,
        company_service=company_service,
        job_service=job_service,
        application_service=application_service,
        interview_service=interview_service,
        curriculum_service=curriculum_service,
        lifecycle=lifecycle,
    )


@pytest.fixture()
def acceptance_runtime(monkeypatch, qtbot, tmp_path) -> AcceptanceRuntime:
    runtime = build_acceptance_runtime(monkeypatch, qtbot, tmp_path / "acd-mvp-acceptance")
    try:
        yield runtime
    finally:
        runtime.close()
