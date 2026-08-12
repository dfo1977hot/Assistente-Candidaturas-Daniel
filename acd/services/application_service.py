from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any
from uuid import uuid4

from acd.core.logger import logger
from acd.domain.entities.application import Application
from acd.infrastructure.repositories.application_repository import ApplicationRepository

_UNCHANGED = object()


class ApplicationService:
    """Camada de serviço para regras de negócio das candidaturas."""

    VALID_STATUSES = {
        "Rascunho",
        "Preparando Currículo",
        "Preparando Carta",
        "Pronta para Aplicação",
        "Aplicada",
        "Em Triagem",
        "Entrevista RH",
        "Teste",
        "Entrevista Técnica",
        "Entrevista Gestor",
        "Oferta",
        "Contratada",
        "Rejeitada",
        "Encerrada",
    }

    VALID_STATUS_TRANSITIONS = {
        "Rascunho": {"Preparando Currículo", "Preparando Carta", "Pronta para Aplicação"},
        "Preparando Currículo": {"Preparando Carta", "Pronta para Aplicação"},
        "Preparando Carta": {"Pronta para Aplicação"},
        "Pronta para Aplicação": {"Aplicada", "Encerrada"},
        "Aplicada": {"Pronta para Aplicação", "Em Triagem", "Rejeitada", "Encerrada"},
        "Em Triagem": {"Entrevista RH", "Rejeitada", "Encerrada"},
        "Entrevista RH": {"Teste", "Entrevista Técnica", "Rejeitada", "Encerrada"},
        "Teste": {"Entrevista Técnica", "Rejeitada", "Encerrada"},
        "Entrevista Técnica": {"Entrevista Gestor", "Rejeitada", "Encerrada"},
        "Entrevista Gestor": {"Oferta", "Rejeitada", "Encerrada"},
        "Oferta": {"Contratada", "Rejeitada", "Encerrada"},
        "Contratada": set(),
        "Rejeitada": set(),
        "Encerrada": set(),
    }

    def __init__(
        self,
        repository: ApplicationRepository | None = None,
        event_dispatcher: Callable[[str, dict[str, Any]], object] | None = None,
    ) -> None:
        self.repository = repository or ApplicationRepository()
        self._event_dispatcher = event_dispatcher

    def set_event_dispatcher(
        self, dispatcher: Callable[[str, dict[str, Any]], object] | None
    ) -> None:
        self._event_dispatcher = dispatcher

    def create_application(
        self,
        *,
        job_id: int,
        company_id: int,
        status: str = "Rascunho",
        application_date: str | None = None,
        next_follow_up: str | None = None,
        response_date: str | None = None,
        interview_date: str | None = None,
        salary_expected: float | None = None,
        salary_offered: float | None = None,
        application_channel: str = "",
        recruiter_name: str = "",
        recruiter_email: str = "",
        recruiter_phone: str = "",
        feedback: str = "",
        notes: str = "",
    ) -> Application:
        """Cria uma candidatura e registra a timeline inicial."""
        self._validate_required_fields(job_id=job_id, company_id=company_id)
        self._validate_status(status)
        application = Application(
            job_id=job_id,
            company_id=company_id,
            status=status,
            application_date=self._parse_optional_date(application_date),
            last_update=date.today(),
            next_follow_up=self._parse_optional_date(next_follow_up),
            response_date=None,
            interview_date=self._parse_optional_date(interview_date),
            salary_expected=salary_expected,
            salary_offered=salary_offered,
            application_channel=application_channel.strip(),
            recruiter_name=recruiter_name.strip(),
            recruiter_email=recruiter_email.strip(),
            recruiter_phone=recruiter_phone.strip(),
            feedback=feedback.strip(),
            notes=notes.strip(),
        )
        created = self.repository.create(application)
        self.repository.add_event(created.id, "created", "Candidatura criada")
        logger.info("Nova candidatura criada: %s", created.id)
        if self._event_dispatcher is not None:
            self._event_dispatcher(
                "application.created",
                {
                    "entity_id": created.id,
                    "application_id": created.id,
                    "job_id": created.job_id,
                    "company_id": created.company_id,
                    "application_status": created.status,
                    "occurrence_id": f"application:{created.id}:created",
                },
            )
        return created

    def update_application(
        self,
        application_id: int,
        *,
        job_id: int,
        company_id: int,
        status: str = "Rascunho",
        application_date: str | None = None,
        next_follow_up: str | None = None,
        response_date: str | None = None,
        interview_date: str | None | object = _UNCHANGED,
        salary_expected: float | None = None,
        salary_offered: float | None = None,
        application_channel: str = "",
        recruiter_name: str = "",
        recruiter_email: str = "",
        recruiter_phone: str = "",
        feedback: str = "",
        notes: str = "",
    ) -> Application | None:
        """Atualiza uma candidatura existente."""
        self._validate_required_fields(job_id=job_id, company_id=company_id)
        self._validate_status(status)
        application = self.repository.get_by_id(application_id)
        if application is None:
            return None

        if application.status != status:
            self._validate_transition(application.status, status)

        application.job_id = job_id
        application.company_id = company_id
        application.status = status
        application.application_date = self._parse_optional_date(application_date)
        application.last_update = date.today()
        application.next_follow_up = self._parse_optional_date(next_follow_up)
        if application.status == "Pronta para Aplicação":
            application.application_date = None
            application.next_follow_up = None
        # Response dates are owned by ApplicationFollowUpService and are only
        # written after an explicitly recorded real response interaction.
        if interview_date is not _UNCHANGED:
            application.interview_date = self._parse_optional_date(interview_date)
        application.salary_expected = salary_expected
        application.salary_offered = salary_offered
        application.application_channel = application_channel.strip()
        application.recruiter_name = recruiter_name.strip()
        application.recruiter_email = recruiter_email.strip()
        application.recruiter_phone = recruiter_phone.strip()
        application.feedback = feedback.strip()
        application.notes = notes.strip()
        updated = self.repository.update(application)
        self.repository.add_event(updated.id, "updated", "Candidatura atualizada")
        logger.info("Candidatura atualizada: %s", updated.id)
        return updated

    def set_interview_date(
        self, application_id: int, interview_date: date | None
    ) -> Application | None:
        """Atualiza a data de entrevista controlada pela agenda de entrevistas."""
        application = self.repository.get_by_id(application_id)
        if application is None:
            return None
        application.interview_date = interview_date
        application.last_update = date.today()
        updated = self.repository.update(application)
        self.repository.add_event(
            application_id,
            "interview_date_synced",
            "Data de entrevista removida"
            if interview_date is None
            else f"Data de entrevista atualizada para {interview_date.isoformat()}",
        )
        return updated

    def delete_application(self, application_id: int, *, delete_linked: bool = False) -> bool:
        """Remove uma candidatura."""
        deleted = self.repository.delete(application_id, delete_linked=delete_linked)
        if deleted:
            logger.info("Candidatura encerrada: %s", application_id)
        return deleted

    def get_application(self, application_id: int) -> Application | None:
        """Retorna uma candidatura pelo ID."""

        return self.repository.get_by_id(application_id)

    def list_applications(self) -> list[Application]:
        """Retorna todas as candidaturas."""
        return self.repository.get_all()

    def search_applications(self, query: str) -> list[Application]:
        """Busca candidaturas por texto."""
        return self.repository.search(query)

    def filter_applications(
        self,
        *,
        status: str | None = None,
        company_id: int | None = None,
        channel: str | None = None,
    ) -> list[Application]:
        """Filtra candidaturas por status, empresa e canal."""
        return self.repository.filter(status=status, company_id=company_id, channel=channel)

    def change_status(
        self, application_id: int, new_status: str, *, administrative: bool = False
    ) -> Application | None:
        """Altera o status seguindo uma máquina de estados simples."""
        application = self.repository.get_by_id(application_id)
        if application is None:
            return None

        current_status = application.status
        self._validate_status(new_status)
        self._validate_transition(current_status, new_status, administrative=administrative)

        updated = self.repository.change_status(
            application_id,
            new_status,
            clear_application_dates=new_status == "Pronta para Aplicação",
        )
        if updated is not None:
            self.repository.add_event(
                application_id, "status_changed", f"Status alterado para {new_status}"
            )
            logger.info("Status alterado: %s", new_status)
            if self._event_dispatcher is not None:
                self._event_dispatcher(
                    "application.status_changed",
                    {
                        "entity_id": updated.id,
                        "application_id": updated.id,
                        "job_id": updated.job_id,
                        "company_id": updated.company_id,
                        "application_status": updated.status,
                        "occurrence_id": str(uuid4()),
                    },
                )
        return updated

    def get_followups(self, application_id: int) -> list[object]:
        """Retorna os eventos de timeline da candidatura."""
        return self.repository.get_followups(application_id)

    def get_statistics(self) -> dict[str, int]:
        """Retorna estatísticas básicas."""
        return self.repository.get_statistics()

    def _validate_required_fields(self, *, job_id: int, company_id: int) -> None:
        if job_id <= 0:
            raise ValueError("Vaga é obrigatória.")
        if company_id <= 0:
            raise ValueError("Empresa é obrigatória.")

    def _validate_status(self, status: str) -> None:
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Status inválido: {status}")

    def _validate_transition(
        self, current_status: str, new_status: str, *, administrative: bool = False
    ) -> None:
        self._validate_status(current_status)
        self._validate_status(new_status)
        allowed = self.VALID_STATUS_TRANSITIONS.get(current_status, set())
        if new_status not in allowed and not administrative:
            raise ValueError(f"Transição inválida de {current_status} para {new_status}.")

    def _parse_optional_date(self, value: str | None) -> date | None:
        if not value:
            return None
        return date.fromisoformat(value)
