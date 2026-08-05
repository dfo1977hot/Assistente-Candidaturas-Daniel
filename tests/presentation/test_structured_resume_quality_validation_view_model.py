"""Pure tests for structured resume quality validation Presentation contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from acd.application.structured_resume_quality_validation import (
    EffectiveStructuredResumeQualityStatus,
    StructuredResumeQualityCategory,
    StructuredResumeQualityIssue,
    StructuredResumeQualitySeverity,
    ValidateEffectiveStructuredResumeQualityResult,
)
from acd.presentation.models.structured_resume_quality_validation_view_state import (
    StructuredResumeQualityValidationViewState,
)
from acd.presentation.pages.structured_resume_quality_validation_view_model import (
    StructuredResumeQualityValidationViewModel,
)


class _UseCase:
    def __init__(self, result: ValidateEffectiveStructuredResumeQualityResult) -> None:
        self.result = result
        self.requests: list[object] = []

    def execute(self, request: object) -> ValidateEffectiveStructuredResumeQualityResult:
        self.requests.append(request)
        return self.result


def _result(
    status: EffectiveStructuredResumeQualityStatus = EffectiveStructuredResumeQualityStatus.SUCCESS,
    *,
    is_valid: bool = True,
    warning_count: int = 0,
    issues: tuple[StructuredResumeQualityIssue, ...] = (),
) -> ValidateEffectiveStructuredResumeQualityResult:
    return ValidateEffectiveStructuredResumeQualityResult(
        status, 11, is_valid=is_valid, score=91, issues=issues,
        error_count=0 if is_valid else 1, warning_count=warning_count,
        info_count=1 if issues else 0, summary="Resumo", message="Mensagem",
    )


def test_view_state_is_immutable_and_contains_only_ui_safe_fields() -> None:
    state = StructuredResumeQualityValidationViewState("success", 11, True, True, 100, (), 0, 0, 0, "Resumo", "Mensagem")

    assert tuple(item.name for item in fields(state)) == (
        "status", "application_id", "is_success", "is_valid", "score", "issues",
        "error_count", "warning_count", "info_count", "summary", "message",
    )
    with pytest.raises(FrozenInstanceError):
        state.score = 0  # type: ignore[misc]


@pytest.mark.parametrize(
    "status",
    tuple(EffectiveStructuredResumeQualityStatus),
)
def test_view_model_maps_real_statuses_and_preserves_result(status: EffectiveStructuredResumeQualityStatus) -> None:
    issue = StructuredResumeQualityIssue("CODE", StructuredResumeQualitySeverity.INFO, StructuredResumeQualityCategory.STRUCTURE, "summary", "content", "Mensagem", "Revisar")
    use_case = _UseCase(_result(status, issues=(issue,)))

    state = StructuredResumeQualityValidationViewModel(use_case).validate(11)  # type: ignore[arg-type]

    assert use_case.requests[0].application_id == 11
    assert state.status == status.value
    assert state.application_id == 11
    assert state.score == 91
    assert state.issues == (issue,)
    assert state.summary == "Resumo"


def test_success_with_warning_uses_attention_message_without_recalculating_score() -> None:
    state = StructuredResumeQualityValidationViewModel(_UseCase(_result(warning_count=1))).validate(11)  # type: ignore[arg-type]

    assert state.is_success
    assert state.is_valid
    assert state.score == 91
    assert state.message == "Validação concluída com pontos de atenção."
