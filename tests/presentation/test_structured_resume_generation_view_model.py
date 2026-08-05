"""Tests for the Presentation mapping of structured resume generation."""

from __future__ import annotations

from acd.application.structured_resume_version_generation import (
    GenerateStructuredResumeVersionResult,
    StructuredResumeVersionGenerationStatus,
)
from acd.presentation.pages.structured_resume_generation_view_model import (
    StructuredResumeGenerationViewModel,
)


class _UseCase:
    def __init__(self, result: GenerateStructuredResumeVersionResult) -> None:
        self.result = result
        self.requests: list[object] = []

    def execute(self, request: object) -> GenerateStructuredResumeVersionResult:
        self.requests.append(request)
        return self.result


def test_view_model_forwards_only_application_id_and_maps_success() -> None:
    use_case = _UseCase(
        GenerateStructuredResumeVersionResult(
            StructuredResumeVersionGenerationStatus.SUCCESS,
            application_id=42,
            resume_version_id=7,
            version="v2",
            explanation="Tailored to the vacancy.",
        )
    )
    view_model = StructuredResumeGenerationViewModel(use_case)  # type: ignore[arg-type]

    state = view_model.generate(42)

    request = use_case.requests[0]
    assert request.application_id == 42
    assert request.optimization_guidance is None
    assert state.is_success
    assert state.resume_version_id == 7
    assert state.version == "v2"


def test_view_model_maps_functional_failure_to_safe_view_state() -> None:
    use_case = _UseCase(
        GenerateStructuredResumeVersionResult(
            StructuredResumeVersionGenerationStatus.PROVIDER_TIMEOUT,
            application_id=42,
        )
    )
    view_model = StructuredResumeGenerationViewModel(use_case)  # type: ignore[arg-type]

    state = view_model.generate(42)

    assert not state.is_success
    assert state.status == "provider_timeout"
    assert state.title == "Tempo esgotado"
    assert "Tente novamente" in state.message
