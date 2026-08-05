"""Infrastructure adapter for application resume selection writes."""

from __future__ import annotations

from acd.application.application_resume_selection_port import ApplicationResumeSelectionPort
from acd.infrastructure.repositories.application_repository import ApplicationRepository


class ApplicationResumeSelectionAdapter(ApplicationResumeSelectionPort):
    """Delegate narrow selection writes to the official application repository."""

    def __init__(self, repository: ApplicationRepository) -> None:
        self._repository = repository

    def set_selected_resume_version(
        self, application_id: int, resume_version_id: int
    ) -> bool:
        """Persist the selected version identifier only."""
        return self._repository.set_selected_resume_version(application_id, resume_version_id)

    def clear_selected_resume_version(self, application_id: int) -> bool:
        """Persist an original-resume selection only."""
        return self._repository.clear_selected_resume_version(application_id)
