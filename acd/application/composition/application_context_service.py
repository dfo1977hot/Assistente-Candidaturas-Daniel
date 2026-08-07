"""Application context composition service."""

from __future__ import annotations

from acd.application.composition.read_models import ApplicationContext
from acd.application.query_ports import ApplicationQueryPort


class ApplicationContextService:
    """Composes an application read model through the Application Query Port."""

    def __init__(self, application_query_port: ApplicationQueryPort) -> None:
        self._application_query_port = application_query_port

    def build(self, application_id: int) -> ApplicationContext | None:
        """Return a serializable context for an existing application."""
        application = self._application_query_port.get_by_id(application_id)
        if application is None:
            return None
        return ApplicationContext(
            application_id=application.application_id,
            job_id=application.job_id,
            company_id=application.company_id,
            status=application.status,
            curriculum_id=application.curriculum_id,
            selected_resume_version_id=application.selected_resume_version_id,
            resume_source=application.resume_source,
            history=tuple(
                {
                    "event_type": entry.event_type,
                    "description": entry.description,
                    "created_at": entry.created_at.isoformat(),
                }
                for entry in self._application_query_port.list_history(application_id)
            ),
        )
