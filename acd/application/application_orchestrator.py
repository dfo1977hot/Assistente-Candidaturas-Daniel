from __future__ import annotations

from typing import Any

from acd.application.application_session import ApplicationSession


class ApplicationOrchestrator:
    """
    Coordena o fluxo de criação de candidaturas.

    Nesta versão, o orquestrador já está preparado para receber
    serviços da camada de aplicação por injeção de dependência.
    """

    def __init__(
        self,
        *,
        company_service: Any | None = None,
        job_service: Any | None = None,
        application_service: Any | None = None,
        job_analysis_service: Any | None = None,
    ) -> None:
        self._session = ApplicationSession()

        self._company_service = company_service
        self._job_service = job_service
        self._application_service = application_service
        self._job_analysis_service = job_analysis_service

    @property
    def session(self) -> ApplicationSession:
        return self._session

    def start_new_application(
        self,
        *,
        company_name: str,
        job_title: str,
        job_description: str,
    ) -> ApplicationSession:
        company_name = company_name.strip()
        job_title = job_title.strip()
        job_description = job_description.strip()

        if not company_name:
            raise ValueError("Company name cannot be empty.")

        if not job_title:
            raise ValueError("Job title cannot be empty.")

        if not job_description:
            raise ValueError("Job description cannot be empty.")

        self._session.reset()

        self._session.company_name = company_name
        self._session.job_title = job_title
        self._session.job_description = job_description

        return self._session

    def clear(self) -> None:
        self._session.reset()

    @property
    def company_service(self) -> Any | None:
        return self._company_service

    @property
    def job_service(self) -> Any | None:
        return self._job_service

    @property
    def application_service(self) -> Any | None:
        return self._application_service

    @property
    def job_analysis_service(self) -> Any | None:
        return self._job_analysis_service