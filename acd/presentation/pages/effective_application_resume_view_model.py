"""Presentation mapping for the effective application resume read model."""

from __future__ import annotations

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.effective_application_resume_use_case import (
    EffectiveApplicationResumeRequest,
    EffectiveApplicationResumeResult,
    EffectiveApplicationResumeUseCase,
)
from acd.presentation.models.effective_application_resume_view_state import (
    EffectiveApplicationResumeViewState,
)


class EffectiveApplicationResumeViewModel:
    """Resolve and map the persisted effective resume for the Presentation layer."""

    def __init__(self, use_case: EffectiveApplicationResumeUseCase) -> None:
        self._use_case = use_case

    def load(self, application_id: int) -> EffectiveApplicationResumeViewState:
        """Load one application without accepting UI selection metadata."""
        return self._map(self._use_case.execute(EffectiveApplicationResumeRequest(application_id)))

    @staticmethod
    def _map(result: EffectiveApplicationResumeResult) -> EffectiveApplicationResumeViewState:
        is_original = result.resume_source is ApplicationResumeSource.ORIGINAL
        available = result.status.value == "success"
        source_label = "Currículo original" if is_original else "Versão adotada"
        return EffectiveApplicationResumeViewState(
            result.status.value,
            result.application_id,
            source_label,
            "" if is_original else result.title,
            result.title or "Currículo efetivamente usado nesta candidatura",
            result.content if available else "",
            result.content_format,
            result.message,
            available,
            is_original,
            not is_original,
        )
