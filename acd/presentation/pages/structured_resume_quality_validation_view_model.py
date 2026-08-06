"""Presentation mapping for effective structured resume quality validation."""

from __future__ import annotations

from acd.application.structured_resume_quality_validation import (
    EffectiveStructuredResumeQualityStatus,
    ValidateEffectiveStructuredResumeQualityRequest,
    ValidateEffectiveStructuredResumeQualityUseCase,
)
from acd.presentation.models.structured_resume_quality_validation_view_state import (
    StructuredResumeQualityValidationViewState,
)


class StructuredResumeQualityValidationViewModel:
    """Map the read-only Application result without duplicating quality rules."""

    def __init__(self, use_case: ValidateEffectiveStructuredResumeQualityUseCase) -> None:
        self._use_case = use_case

    def validate(self, application_id: int) -> StructuredResumeQualityValidationViewState:
        """Validate one effective resume using only its application identifier."""
        result = self._use_case.execute(ValidateEffectiveStructuredResumeQualityRequest(application_id))
        message = result.message
        if result.status is EffectiveStructuredResumeQualityStatus.SUCCESS and result.is_valid and result.warning_count:
            message = "Validação concluída com pontos de atenção."
        return StructuredResumeQualityValidationViewState(
            result.status.value,
            result.application_id,
            result.status is EffectiveStructuredResumeQualityStatus.SUCCESS,
            result.is_valid,
            result.score,
            result.issues,
            result.error_count,
            result.warning_count,
            result.info_count,
            result.summary,
            message,
        )
