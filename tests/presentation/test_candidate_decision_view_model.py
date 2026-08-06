"""Tests for the Candidate Decision Presentation contract."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import inspect

import pytest

from acd.application.candidate_decision_service import (
    CandidateDecision,
    CandidateDecisionResult,
    DecisionConfidence,
)
from acd.presentation.pages.candidate_decision_view_model import CandidateDecisionViewModel


class DecisionUseCaseFixture:
    """Small Application boundary fixture for Presentation tests."""

    def __init__(self, result: CandidateDecisionResult) -> None:
        self._result = result
        self.application_ids: list[int] = []

    def execute(self, application_id: int) -> CandidateDecisionResult:
        self.application_ids.append(application_id)
        return self._result


def _result(decision: CandidateDecision) -> CandidateDecisionResult:
    return CandidateDecisionResult(
        application_id=1,
        decision=decision,
        score=None if decision is CandidateDecision.INSUFFICIENT_DATA else 82.0,
        confidence=DecisionConfidence.LOW if decision is CandidateDecision.INSUFFICIENT_DATA else DecisionConfidence.HIGH,
        strengths=("Persisted ATS score is 82.00.",),
        risks=("Missing skill: Docker.",),
        gaps=("Docker",),
        recommendations=("Highlight Python.",),
        reasons=("Fixture reason.",),
    )


@pytest.mark.parametrize(
    ("decision", "headline"),
    [
        (CandidateDecision.STRONG_APPLY, "Strong application"),
        (CandidateDecision.REVIEW, "Review application"),
        (CandidateDecision.LOW_PRIORITY, "Low priority"),
        (CandidateDecision.INSUFFICIENT_DATA, "Insufficient data"),
    ],
)
def test_view_model_maps_application_decision_to_immutable_view_state(
    decision: CandidateDecision,
    headline: str,
) -> None:
    use_case = DecisionUseCaseFixture(_result(decision))

    state = CandidateDecisionViewModel(use_case).load(7)  # type: ignore[arg-type]

    assert use_case.application_ids == [7]
    assert state.decision == decision.value
    assert state.headline == headline
    assert state.score == _result(decision).score
    assert state.confidence == _result(decision).confidence.value
    assert state.reasons == ("Fixture reason.",)
    with pytest.raises(FrozenInstanceError):
        state.headline = "Changed"  # type: ignore[misc]


def test_view_model_depends_only_on_the_authorized_application_contract() -> None:
    source = inspect.getsource(CandidateDecisionViewModel)

    assert "CandidateDecisionUseCase" in source
    assert "acd.infrastructure" not in source
    assert "CandidateDecisionService" not in source
    assert "composition" not in source
