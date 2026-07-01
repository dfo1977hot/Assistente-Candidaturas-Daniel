from __future__ import annotations

from datetime import date
from typing import Optional

from acd.core.logger import logger
from acd.domain.entities.application import Application
from acd.infrastructure.repositories.application_repository import ApplicationRepository


class ApplicationService:
    """Camada de serviço para regras de negócio das candidaturas."""

    VALID_STATUS_TRANSITIONS = {
        "Rascunho": {"Preparando Currículo", "Preparando Carta", "Pronta para Aplicação"},
        "Preparando Currículo": {"Preparando Carta", "Pronta para Aplicação"},
        "Preparando Carta": {"Pronta para Aplicação"},
        "Pronta para Aplicação": {"Aplicada", "Encerrada"},
        "Aplicada": {"Em Triagem", "Rejeitada", "Encerrada"},
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

    def __init__(self, repository: Optional[ApplicationRepository] = None) -> None:
        self.repository = repository or ApplicationRepository()

    def create_application(
        self,
        *,
        job_id: int,
        company_id: int,
        status: str = "Rascunho",
        application_date: Optional[str] = None,
        next_follow_up: Optional[str] = None,
        response_date: Optional[str] = None,
        interview_date: Optional[str] = None,
        salary_expected: Optional[float] = None,
        salary_offered: Optional[float] = None,
        application_channel: str = "",
        recruiter_name: str = "",
        recruiter_email: str = "",
        recruiter_phone: str = "",
        feedback: str = "",
        notes: str = "",
    ) -> Application:
        """Cria uma candidatura e registra a timeline inicial."""
        self._validate_required_fields(job_id=job_id, company_id=company_id)
        application = Application(
            job_id=job_id,
            company_id=company_id,
            status=status,
            application_date=self._parse_optional_date(application_date),
            last_update=date.today(),
            next_follow_up=self._parse_optional_date(next_follow_up),
            response_date=self._parse_optional_date(response_date),
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
        return created

    def update_application(
        self,
        application_id: int,
        *,
        job_id: int,
        company_id: int,
        status: str = "Rascunho",
        application_date: Optional[str] = None,
        next_follow_up: Optional[str] = None,
        response_date: Optional[str] = None,
        interview_date: Optional[str] = None,
        salary_expected: Optional[float] = None,
        salary_offered: Optional[float] = None,
        application_channel: str = "",
        recruiter_name: str = "",
        recruiter_email: str = "",
        recruiter_phone: str = "",
        feedback: str = "",
        notes: str = "",
    ) -> Optional[Application]:
        """Atualiza uma candidatura existente."""
        self._validate_required_fields(job_id=job_id, company_id=company_id)
        application = self.repository.get_by_id(application_id)
        if application is None:
            return None

        application.job_id = job_id
        application.company_id = company_id
        application.status = status
        application.application_date = self._parse_optional_date(application_date)
        application.last_update = date.today()
        application.next_follow_up = self._parse_optional_date(next_follow_up)
        application.response_date = self._parse_optional_date(response_date)
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

    def delete_application(self, application_id: int) -> bool:
        """Remove uma candidatura."""
        deleted = self.repository.delete(application_id)
        if deleted:
            logger.info("Candidatura encerrada: %s", application_id)
        return deleted

    def list_applications(self) -> list[Application]:
        """Retorna todas as candidaturas."""
        return self.repository.get_all()

    def search_applications(self, query: str) -> list[Application]:
        """Busca candidaturas por texto."""
        return self.repository.search(query)

    def filter_applications(self, *, status: Optional[str] = None, company_id: Optional[int] = None, channel: Optional[str] = None) -> list[Application]:
        """Filtra candidaturas por status, empresa e canal."""
        return self.repository.filter(status=status, company_id=company_id, channel=channel)

    def change_status(self, application_id: int, new_status: str, *, administrative: bool = False) -> Optional[Application]:
        """Altera o status seguindo uma máquina de estados simples."""
        application = self.repository.get_by_id(application_id)
        if application is None:
            return None

        current_status = application.status
        allowed = self.VALID_STATUS_TRANSITIONS.get(current_status, set())
        if new_status not in allowed and not administrative:
            raise ValueError(f"Transição inválida de {current_status} para {new_status}.")

        updated = self.repository.change_status(application_id, new_status)
        if updated is not None:
            self.repository.add_event(application_id, "status_changed", f"Status alterado para {new_status}")
            logger.info("Status alterado: %s", new_status)
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

    def _parse_optional_date(self, value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        return date.fromisoformat(value)
