from __future__ import annotations

from acd.application.application_orchestrator import ApplicationOrchestrator
from acd.application.application_session import ApplicationSession


class StartApplicationUseCase:
    """
    Caso de uso responsável por iniciar uma nova candidatura.

    Atualmente delega ao ApplicationOrchestrator.
    Futuramente poderá executar validações adicionais,
    consultar serviços e persistir entidades.
    """

    def __init__(
        self,
        orchestrator: ApplicationOrchestrator,
    ) -> None:
        self._orchestrator = orchestrator

    def execute(
        self,
        *,
        company_name: str,
        job_title: str,
        job_description: str,
    ) -> ApplicationSession:
        return self._orchestrator.start_new_application(
            company_name=company_name,
            job_title=job_title,
            job_description=job_description,
        )