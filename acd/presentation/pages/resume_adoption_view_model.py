"""Presentation adapter for explicit resume adoption commands."""

from __future__ import annotations

from acd.application.resume_adoption_use_cases import (
    AdoptResumeVersionRequest,
    AdoptResumeVersionUseCase,
    ResumeAdoptionResult,
    UseOriginalResumeRequest,
    UseOriginalResumeUseCase,
)
from acd.presentation.models.resume_adoption_view_state import ResumeAdoptionViewState


class ResumeAdoptionViewModel:
    """Map existing Application adoption use cases to immutable UI state."""

    def __init__(
        self,
        adopt_resume_version_use_case: AdoptResumeVersionUseCase,
        use_original_resume_use_case: UseOriginalResumeUseCase,
    ) -> None:
        self._adopt_resume_version_use_case = adopt_resume_version_use_case
        self._use_original_resume_use_case = use_original_resume_use_case

    def adopt(self, application_id: int, resume_version_id: int) -> ResumeAdoptionViewState:
        """Persist one explicit selection through the existing use case."""
        return self._map(
            self._adopt_resume_version_use_case.execute(
                AdoptResumeVersionRequest(application_id, resume_version_id)
            )
        )

    def use_original(self, application_id: int) -> ResumeAdoptionViewState:
        """Explicitly clear the selection through the existing use case."""
        return self._map(
            self._use_original_resume_use_case.execute(UseOriginalResumeRequest(application_id))
        )

    @staticmethod
    def _map(result: ResumeAdoptionResult) -> ResumeAdoptionViewState:
        """Keep Application result metadata intact while providing a concise title."""
        title = "Currículo atualizado" if result.status.value in {"success", "already_selected"} else "Não foi possível atualizar o currículo"
        return ResumeAdoptionViewState(
            status=result.status.value,
            application_id=result.application_id,
            resume_source=result.resume_source,
            selected_resume_version_id=result.selected_resume_version_id,
            title=title,
            message=result.message,
        )
