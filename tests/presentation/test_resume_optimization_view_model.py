"""Tests for the explicit resume optimization Presentation boundary."""

from __future__ import annotations

from acd.application.resume_optimization.resume_optimization_use_case import (
    ResumeOptimizationResult,
)
from acd.application.resume_optimization.resume_optimization_workflow import (
    ResumeOptimizationAvailability,
)
from acd.presentation.pages.resume_optimization_view_model import ResumeOptimizationViewModel


class _UseCase:
    def __init__(self, result: ResumeOptimizationResult) -> None:
        self.result = result
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return self.result


def test_view_model_creates_an_explicit_request_and_maps_success() -> None:
    use_case = _UseCase(ResumeOptimizationResult(4, ResumeOptimizationAvailability.READY, "v2.0"))

    state = ResumeOptimizationViewModel(use_case).optimize(4)

    assert use_case.requests[0].application_id == 4
    assert state.success
    assert state.version == "v2.0"


def test_view_model_maps_functional_prerequisites() -> None:
    use_case = _UseCase(ResumeOptimizationResult(4, ResumeOptimizationAvailability.ATS_REQUIRED))

    state = ResumeOptimizationViewModel(use_case).optimize(4)

    assert not state.success
    assert state.status == "ats_required"
