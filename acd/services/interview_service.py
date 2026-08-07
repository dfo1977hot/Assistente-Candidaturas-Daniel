from __future__ import annotations

from datetime import datetime, timedelta

from acd.core.logger import logger
from acd.domain.entities.interview import Interview
from acd.infrastructure.repositories.interview_repository import InterviewRepository
from acd.services.application_service import ApplicationService


class InterviewService:
    """Serviço para cadastro, validação e agenda de entrevistas."""

    VALID_INTERVIEW_TYPES = {"RH", "Gestor", "Técnica", "Painel", "Case", "Teste Prático", "Final"}
    VALID_RESULTS = {"Agendada", "Realizada", "Aprovada", "Reprovada", "Cancelada", "Reagendada"}

    def __init__(self, repository: InterviewRepository | None = None) -> None:
        self.repository = repository or InterviewRepository()
        self.application_service = ApplicationService()

    def create_interview(
        self,
        *,
        application_id: int,
        interview_date: datetime,
        interview_type: str,
        interviewer: str = "",
        interviewer_email: str = "",
        meeting_link: str = "",
        location: str = "",
        duration: str = "",
        notes: str = "",
        feedback: str = "",
        result: str = "Agendada",
    ) -> Interview:
        """Cria uma entrevista e registra a timeline da candidatura."""
        parsed_date = self._parse_datetime(interview_date)
        self._validate_required_fields(
            application_id=application_id, interview_date=parsed_date, interview_type=interview_type
        )
        self._validate_type(interview_type)
        self._validate_result(result)
        interview = Interview(
            application_id=application_id,
            interview_date=parsed_date,
            interview_type=interview_type,
            interviewer=interviewer.strip(),
            interviewer_email=interviewer_email.strip(),
            meeting_link=meeting_link.strip(),
            location=location.strip(),
            duration=duration.strip(),
            notes=notes.strip(),
            feedback=feedback.strip(),
            result=result,
        )
        created = self.repository.create(interview)
        self.application_service.repository.add_event(
            application_id, "interview_scheduled", f"Entrevista agendada ({interview_type})"
        )
        logger.info("Entrevista criada: %s", created.id)
        return created

    def update_interview(
        self,
        interview_id: int,
        *,
        application_id: int,
        interview_date: datetime,
        interview_type: str,
        interviewer: str = "",
        interviewer_email: str = "",
        meeting_link: str = "",
        location: str = "",
        duration: str = "",
        notes: str = "",
        feedback: str = "",
        result: str = "Agendada",
    ) -> Interview | None:
        """Atualiza uma entrevista existente."""
        parsed_date = self._parse_datetime(interview_date)
        self._validate_required_fields(
            application_id=application_id, interview_date=parsed_date, interview_type=interview_type
        )
        interview = self.repository.get_by_id(interview_id)
        if interview is None:
            return None
        interview.application_id = application_id
        interview.interview_date = parsed_date
        interview.interview_type = interview_type
        interview.interviewer = interviewer.strip()
        interview.interviewer_email = interviewer_email.strip()
        interview.meeting_link = meeting_link.strip()
        interview.location = location.strip()
        interview.duration = duration.strip()
        interview.notes = notes.strip()
        interview.feedback = feedback.strip()
        interview.result = result
        updated = self.repository.update(interview)
        self.application_service.repository.add_event(
            application_id, "interview_updated", f"Entrevista atualizada ({interview_type})"
        )
        logger.info("Entrevista atualizada: %s", updated.id)
        return updated

    def delete_interview(self, interview_id: int) -> bool:
        """Remove uma entrevista."""
        deleted = self.repository.delete(interview_id)
        if deleted:
            logger.info("Entrevista removida: %s", interview_id)
        return deleted

    def list_interviews(self) -> list[Interview]:
        """Lista todas as entrevistas."""
        return self.repository.get_all()

    def search_interviews(self, query: str) -> list[Interview]:
        """Pesquisa entrevistas."""
        return self.repository.search(query)

    def filter_interviews(
        self,
        *,
        interview_type: str | None = None,
        result: str | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> list[Interview]:
        """Filtra entrevistas."""
        return self.repository.filter(
            interview_type=interview_type,
            result=result,
            period_start=period_start,
            period_end=period_end,
        )

    def get_today_interviews(self) -> list[Interview]:
        """Retorna entrevistas do dia."""
        return self.repository.get_today()

    def get_upcoming_interviews(self, limit: int = 5) -> list[Interview]:
        """Retorna as próximas entrevistas."""
        return self.repository.get_next(limit)

    def get_statistics(self) -> dict[str, int]:
        """Retorna estatísticas de agenda."""
        return self.repository.get_statistics()

    def get_reminders(self, *, hours: int = 24) -> list[Interview]:
        """Retorna entrevistas próximas em um horizonte de tempo."""
        threshold = datetime.now() + timedelta(hours=hours)
        interviews = self.repository.get_all()
        return [
            interview
            for interview in interviews
            if datetime.now() <= interview.interview_date <= threshold
            and interview.result == "Agendada"
        ]

    def _validate_required_fields(
        self, *, application_id: int, interview_date: datetime, interview_type: str
    ) -> None:
        if application_id <= 0:
            raise ValueError("Candidatura é obrigatória.")
        if interview_date is None:
            raise ValueError("Data da entrevista é obrigatória.")
        if not interview_type or not interview_type.strip():
            raise ValueError("Tipo da entrevista é obrigatório.")

    def _parse_datetime(self, value: object) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        raise ValueError("Data da entrevista inválida.")

    def _validate_type(self, interview_type: str) -> None:
        if interview_type not in self.VALID_INTERVIEW_TYPES:
            raise ValueError(f"Tipo inválido: {interview_type}")

    def _validate_result(self, result: str) -> None:
        if result not in self.VALID_RESULTS:
            raise ValueError(f"Resultado inválido: {result}")
