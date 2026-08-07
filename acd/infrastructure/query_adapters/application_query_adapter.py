"""Infrastructure adapter for application read queries."""

from __future__ import annotations

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.query_ports import (
    ApplicationHistoryQueryDTO,
    ApplicationQueryDTO,
    ApplicationQueryPort,
)
from acd.infrastructure.repositories.application_repository import ApplicationRepository


class ApplicationQueryAdapter(ApplicationQueryPort):
    """Maps existing application repository reads to Application DTOs."""

    def __init__(self, repository: ApplicationRepository) -> None:
        self._repository = repository

    def get_by_id(self, application_id: int) -> ApplicationQueryDTO | None:
        """Return an application DTO when the repository has the requested entity."""
        application = self._repository.get_by_id(application_id)
        if application is None:
            return None
        selected_resume_version_id = getattr(application, "selected_resume_version_id", None)
        return ApplicationQueryDTO(
            application_id=application.id,
            job_id=application.job_id,
            company_id=application.company_id,
            curriculum_id=application.curriculum_id,
            curriculum_version=application.curriculum_version,
            status=application.status,
            selected_resume_version_id=selected_resume_version_id,
            resume_source=ApplicationResumeSource.from_selection(selected_resume_version_id),
        )

    def list_history(self, application_id: int) -> tuple[ApplicationHistoryQueryDTO, ...]:
        """Return application timeline entries as immutable DTOs."""
        return tuple(
            ApplicationHistoryQueryDTO(
                event_type=event.event_type,
                description=event.description,
                created_at=event.created_at,
            )
            for event in self._repository.get_followups(application_id)
        )
