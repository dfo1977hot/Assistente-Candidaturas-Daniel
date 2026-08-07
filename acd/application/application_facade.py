from __future__ import annotations

from acd.application.application_orchestrator import ApplicationOrchestrator
from acd.application.application_session import ApplicationSession
from acd.application.application_snapshot import ApplicationSnapshot
from acd.application.start_application_use_case import (
    StartApplicationUseCase,
)


class ApplicationFacade:
    """
    Fachada da camada de aplicação.

    Centraliza o acesso aos casos de uso relacionados ao fluxo de
    candidatura, oferecendo uma interface simples para a camada de
    apresentação.
    """

    def __init__(
        self,
        orchestrator: ApplicationOrchestrator | None = None,
    ) -> None:
        self._orchestrator = orchestrator or ApplicationOrchestrator()
        self._start_application = StartApplicationUseCase(
            self._orchestrator
        )

    @property
    def session(self) -> ApplicationSession:
        """
        Retorna a sessão atual da candidatura.
        """
        return self._orchestrator.session

    def snapshot(self) -> ApplicationSnapshot:
        """
        Retorna uma representação somente leitura da sessão.
        """
        session = self.session

        return ApplicationSnapshot(
            company_name=session.company_name,
            job_title=session.job_title,
            job_url=session.job_url,
            job_description=session.job_description,
            is_analyzed=session.is_analyzed,
            has_resume=session.has_resume,
            is_registered=session.is_registered,
        )

    def start_application(
        self,
        *,
        company_name: str,
        job_title: str,
        job_description: str,
    ) -> ApplicationSession:
        """
        Inicia uma nova candidatura.
        """
        return self._start_application.execute(
            company_name=company_name,
            job_title=job_title,
            job_description=job_description,
        )

    def clear(self) -> None:
        """
        Limpa completamente a sessão atual.
        """
        self._orchestrator.clear()

    def update_company_name(self, company_name: str) -> None:
        self.session.company_name = company_name.strip()

    def update_job_title(self, job_title: str) -> None:
        self.session.job_title = job_title.strip()

    def update_job_url(self, job_url: str) -> None:
        self.session.job_url = job_url.strip()

    def update_job_description(self, job_description: str) -> None:
        self.session.job_description = job_description.strip()