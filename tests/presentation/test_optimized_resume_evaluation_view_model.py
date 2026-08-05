"""Tests for optimized resume evaluation Presentation mappings."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import inspect

import pytest

from acd.application.optimized_resume_evaluation_use_case import (
    OptimizedResumeEvaluationResult,
    OptimizedResumeEvaluationStatus,
)
from acd.presentation.pages.optimized_resume_evaluation_view_model import (
    OptimizedResumeEvaluationViewModel,
)


class _UseCase:
    def __init__(self, result: OptimizedResumeEvaluationResult) -> None:
        self.result = result
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return self.result


def test_maps_success_to_transient_view_state() -> None:
    use_case = _UseCase(
        OptimizedResumeEvaluationResult(
            OptimizedResumeEvaluationStatus.SUCCESS,
            4,
            9,
            12,
            55.0,
            70.0,
            15.0,
            "improved",
            persisted=False,
        )
    )

    state = OptimizedResumeEvaluationViewModel(use_case).evaluate(4, 12)  # type: ignore[arg-type]

    assert use_case.requests[0].application_id == 4
    assert use_case.requests[0].resume_version_id == 12
    assert state.title == "Avaliação atual da versão selecionada"
    assert state.persisted is False
    assert state.score_delta == 15.0
    with pytest.raises(FrozenInstanceError):
        state.persisted = True  # type: ignore[misc]


def test_maps_functional_precondition() -> None:
    state = OptimizedResumeEvaluationViewModel(
        _UseCase(
            OptimizedResumeEvaluationResult(
                OptimizedResumeEvaluationStatus.ATS_ORIGINAL_REQUIRED,
                4,
            )
        )
    ).evaluate(4, 12)  # type: ignore[arg-type]

    assert state.status == "ats_original_required"
    assert "ATS original" in state.title


def test_view_model_keeps_the_presentation_boundary() -> None:
    source = inspect.getsource(OptimizedResumeEvaluationViewModel)

    for forbidden_name in (
        "ATSEvaluator",
        "ATSService",
        "DependencyContainer",
        "acd.infrastructure",
        "QWidget",
    ):
        assert forbidden_name not in source
