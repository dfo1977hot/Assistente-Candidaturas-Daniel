"""Infrastructure adapter for interview read queries."""

from __future__ import annotations

from acd.application.query_ports import InterviewQueryDTO, InterviewQueryPort
from acd.infrastructure.repositories.interview_repository import InterviewRepository


class InterviewQueryAdapter(InterviewQueryPort):
    """Maps existing interview repository reads to Application DTOs."""

    def __init__(self, repository: InterviewRepository) -> None:
        self._repository = repository

    def list_by_application(self, application_id: int) -> tuple[InterviewQueryDTO, ...]:
        """Return existing interviews associated with an application as DTOs."""
        return tuple(
            InterviewQueryDTO(
                interview_id=interview.id,
                application_id=interview.application_id,
                interview_date=interview.interview_date,
                interview_type=interview.interview_type,
                result=interview.result,
            )
            for interview in self._repository.get_all()
            if interview.application_id == application_id
        )
