"""Presentation mapping for the read-only resume version review."""

from __future__ import annotations

from acd.application.resume_version_review_use_case import (
    ResumeVersionReviewResult,
    ResumeVersionReviewStatus,
    ResumeVersionReviewUseCase,
)
from acd.presentation.models.resume_version_review_view_state import (
    ResumeVersionItemViewState,
    ResumeVersionReviewViewState,
)


class ResumeVersionReviewViewModel:
    """Map review results into immutable Presentation state."""

    _MESSAGES: dict[ResumeVersionReviewStatus, tuple[str, str]] = {
        ResumeVersionReviewStatus.APPLICATION_NOT_FOUND: (
            "Candidatura não encontrada",
            "A candidatura selecionada não está disponível.",
        ),
        ResumeVersionReviewStatus.CURRICULUM_REQUIRED: (
            "Currículo necessário",
            "Associe um currículo à candidatura.",
        ),
        ResumeVersionReviewStatus.NO_VERSIONS: (
            "Versões deste currículo",
            "Nenhuma versão gerada para este currículo.",
        ),
        ResumeVersionReviewStatus.VERSION_NOT_FOUND: (
            "Versão não encontrada",
            "A versão selecionada não pertence a este currículo.",
        ),
        ResumeVersionReviewStatus.SUCCESS: ("Versões deste currículo", ""),
    }

    def __init__(self, use_case: ResumeVersionReviewUseCase) -> None:
        self._use_case = use_case

    def load(self, application_id: int) -> ResumeVersionReviewViewState:
        """Load the deterministic default version for an application curriculum."""
        return self._map(self._use_case.execute(application_id))

    def select_version(
        self,
        application_id: int,
        version_id: int,
    ) -> ResumeVersionReviewViewState:
        """Map a visual-only version selection into Presentation state."""
        return self._map(self._use_case.execute(application_id, version_id))

    def _map(self, result: ResumeVersionReviewResult) -> ResumeVersionReviewViewState:
        title, message = self._MESSAGES[result.status]
        selected_version = result.selected_version
        return ResumeVersionReviewViewState(
            status=result.status.value,
            title=title,
            message=message,
            application_id=result.application_id,
            original_content=result.original_content,
            versions=tuple(
                ResumeVersionItemViewState(
                    version_id=version.version_id,
                    label=version.version,
                )
                for version in result.versions
            ),
            selected_version_id=(
                None if selected_version is None else selected_version.version_id
            ),
            selected_content="" if selected_version is None else selected_version.content,
            explanation="" if selected_version is None else selected_version.explanation,
            resume_source=result.resume_source,
            selected_resume_version_id=result.selected_resume_version_id,
        )
