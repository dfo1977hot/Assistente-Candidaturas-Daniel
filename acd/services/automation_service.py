from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from acd.core.logger import logger
from acd.domain.automation.application_result import ApplicationResult
from acd.domain.automation.execution_log import ExecutionLog
from acd.domain.entities.application import Application
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job import Job
from acd.domain.entities.job_profile import JobProfile
from acd.infrastructure.automation.browser_manager import BrowserManager
from acd.infrastructure.automation.connector_factory import ConnectorFactory
from acd.infrastructure.repositories.application_repository import ApplicationRepository


@dataclass(slots=True)
class AutomationContext:
    """Contexto compartilhado por uma execução de automação."""

    application: Application
    curriculum: Curriculum
    job: Job
    job_profile: JobProfile
    platform: str
    headless: bool = True
    browser: str = "chromium"


class AutomationService:
    """Motor principal de automação de candidaturas."""

    def __init__(
        self,
        repository: ApplicationRepository | None = None,
        browser_manager: BrowserManager | None = None,
        connector_factory: ConnectorFactory | None = None,
    ) -> None:
        self.repository = repository or ApplicationRepository()
        self.browser_manager = browser_manager or BrowserManager()
        self.connector_factory = connector_factory or ConnectorFactory()

    def run(self, context: AutomationContext) -> dict[str, Any]:
        """Executa a candidatura para a plataforma indicada."""
        browser_context = self.browser_manager.create_context(headless=context.headless)
        connector = self.connector_factory.create(context.platform)
        if connector is None:
            raise ValueError("Plataforma não suportada")

        logs: list[ExecutionLog] = []
        logs.append(ExecutionLog(event="started", details="Iniciando execução"))
        logs.append(
            ExecutionLog(
                event="browser",
                details=f"Browser {browser_context['browser']} headless={browser_context['headless']}",
            )
        )

        connector.login()
        logs.append(ExecutionLog(event="login", details="Login realizado"))
        connector.open_job("https://example.com/job")
        logs.append(ExecutionLog(event="open_job", details="Vaga aberta"))
        connector.fill_form()
        logs.append(ExecutionLog(event="fill_form", details="Formulário preenchido"))
        connector.upload_resume("resume.pdf")
        logs.append(ExecutionLog(event="upload_resume", details="Currículo anexado"))
        connector.upload_cover_letter("cover_letter.pdf")
        logs.append(ExecutionLog(event="upload_cover_letter", details="Carta anexada"))
        connector.submit()
        logs.append(ExecutionLog(event="submit", details="Envio realizado"))
        result_data = connector.capture_result()
        logs.append(ExecutionLog(event="result", details=str(result_data)))

        screenshot_path = self._save_screenshot(context)
        self._update_application_status(context.application.id, "Aplicada")
        logger.info("Aplicação automatizada concluída para %s", context.platform)
        return {
            "status": "success",
            "result": ApplicationResult(
                status="success", message="Aplicação concluída", screenshot_path=screenshot_path
            ),
            "logs": [{"event": log.event, "details": log.details} for log in logs],
        }

    def _save_screenshot(self, context: AutomationContext) -> str:
        path = (
            Path("data/automation/screenshots")
            / f"{context.platform}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.png"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")
        return str(path)

    def _update_application_status(self, application_id: int | None, status: str) -> None:
        if application_id is None:
            return
        self.repository.change_status(application_id, status)
