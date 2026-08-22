"""Desktop window layout; dependency composition belongs to the composition root."""

from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QWidget,
)

from acd.core.router import Router
from acd.services.settings_service import SettingsService


class MainWindow(QMainWindow):
    """Organize pre-built Presentation objects without creating application dependencies."""

    def __init__(
        self,
        *,
        sidebar: QListWidget,
        router: Router,
        pages: Mapping[str, QWidget],
        settings_service: SettingsService,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Assistente de Candidaturas do Daniel")
        self.resize(1400, 800)
        self._settings_service = settings_service
        startup_method = (
            self.showMinimized
            if self._settings_service.startup_mode() == "minimized"
            else self.showMaximized
        )
        QTimer.singleShot(0, startup_method)

        self.sidebar = sidebar
        self.stack = QStackedWidget()
        self.router = router
        self.router.set_stack(self.stack)

        for name, page in pages.items():
            self.router.register(name, page)
            setattr(self, f"{name}_page", page)

        self.dashboard = pages["dashboard"]
        self.company_page = pages["companies"]
        self.job_page = pages["jobs"]
        self.application_page = pages["applications"]
        self.interview_page = pages["interviews"]
        self.curriculum_page = pages["curricula"]
        self.workflow_page = pages["workflows"]
        self.analytics_page = pages["analytics"]
        self.career_page = pages["career"]
        self.assistant_page = pages["assistant"]
        self.agent_console_page = pages["agent_console"]
        self.cover_letters_page = pages["cover_letters"]
        self.crm_page = pages["crm"]
        self.candidate_profile_page = pages["candidate_profile"]
        self.settings_page = pages["settings"]

        self.sidebar.itemClicked.connect(self._on_sidebar_item_clicked)
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)
        self.setCentralWidget(central)

        status = QStatusBar()
        from acd.version import get_version

        status.showMessage(f"ACD v{get_version()}")
        self.setStatusBar(status)

    def showEvent(self, event: object) -> None:
        super().showEvent(event)
        start_scheduler = getattr(self.workflow_page, "start_scheduler", None)
        if callable(start_scheduler):
            start_scheduler()

    def closeEvent(self, event: object) -> None:
        shutdown_dashboard = getattr(self.dashboard, "shutdown", None)
        if callable(shutdown_dashboard):
            shutdown_dashboard()
        super().closeEvent(event)

    def _on_sidebar_item_clicked(self, item: object) -> None:
        label = item.text()
        destinations = (
            ("Empresas", "companies"), ("Vagas", "jobs"), ("Candidaturas", "applications"),
            ("Entrevistas", "interviews"), ("Currículos", "curricula"), ("Workflow", "workflows"),
            ("Análise", "analytics"), ("Analytics", "analytics"), ("Planejamento", "career"),
            ("Carreira", "career"), ("Assistente", "assistant"), ("IA", "assistant"),
            ("Agentes", "agent_console"), ("Cartas", "cover_letters"), ("CRM", "crm"),
            ("Perfil do Candidato", "candidate_profile"), ("Config", "settings"), ("Dashboard", "dashboard"),
        )
        for text, destination in destinations:
            if text in label:
                page = getattr(self, f"{destination}_page", None)
                refresh = getattr(page, "refresh_reference_data", None)
                if callable(refresh):
                    refresh()
                self.router.navigate(destination)
                return

    def navigate_candidate_decision_action(self, action_id: str) -> None:
        destinations = {
            "review_gaps": "career",
            "prepare_curriculum": "curricula",
            "prepare_interview": "interviews",
        }
        if destination := destinations.get(action_id):
            self.router.navigate(destination)
