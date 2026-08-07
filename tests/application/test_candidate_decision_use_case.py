"""Tests for the Candidate Decision Support application entry point."""

from __future__ import annotations

import inspect

from acd.application.candidate_decision_service import (
    CandidateDecision,
    CandidateDecisionResult,
    DecisionConfidence,
)
from acd.application.candidate_decision_use_case import CandidateDecisionUseCase


class RecordingCandidateDecisionService:
    """Small Application-service fixture for use-case delegation tests."""

    def __init__(self, result: CandidateDecisionResult) -> None:
        self.result = result
        self.application_ids: list[int] = []

    def assess(self, application_id: int) -> CandidateDecisionResult:
        self.application_ids.append(application_id)
        return self.result


def _result(decision: CandidateDecision) -> CandidateDecisionResult:
    return CandidateDecisionResult(
        application_id=1,
        decision=decision,
        score=None if decision is CandidateDecision.INSUFFICIENT_DATA else 82.0,
        confidence=(
            DecisionConfidence.LOW
            if decision is CandidateDecision.INSUFFICIENT_DATA
            else DecisionConfidence.HIGH
        ),
        strengths=(),
        risks=(),
        gaps=(),
        recommendations=(),
        reasons=("Fixture decision.",),
    )


def test_execute_delegates_to_the_single_candidate_decision_service() -> None:
    """The use case forwards the identifier and preserves the service result."""
    expected = _result(CandidateDecision.STRONG_APPLY)
    service = RecordingCandidateDecisionService(expected)

    result = CandidateDecisionUseCase(service).execute(1)  # type: ignore[arg-type]

    assert result is expected
    assert service.application_ids == [1]


def test_execute_preserves_insufficient_data_for_missing_or_incomplete_contexts() -> None:
    """Missing application, ATS, resume, or vacancy stays explicit to consumers."""
    expected = _result(CandidateDecision.INSUFFICIENT_DATA)
    service = RecordingCandidateDecisionService(expected)

    result = CandidateDecisionUseCase(service).execute(99)  # type: ignore[arg-type]

    assert result.decision is CandidateDecision.INSUFFICIENT_DATA
    assert result.confidence is DecisionConfidence.LOW
    assert service.application_ids == [99]


def test_candidate_decision_use_case_has_no_infrastructure_dependency() -> None:
    """The entry point remains independent from persistence and adapters."""
    assert "acd.infrastructure" not in inspect.getsource(CandidateDecisionUseCase)
