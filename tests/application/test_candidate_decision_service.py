"""Tests for deterministic Candidate Decision Support."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict
import inspect
import json

import pytest

from acd.application.candidate_decision_service import (
    CandidateDecision,
    CandidateDecisionResult,
    CandidateDecisionService,
    DecisionConfidence,
)
from acd.application.composition.read_models import (
    ApplicationContext,
    ATSContext,
    CompanyContext,
    GapContext,
    InterviewContext,
    ResumeContext,
    VacancyContext,
)

_DEFAULT_GAPS = GapContext()
_DEFAULT_RESUME = ResumeContext(4, "v1", "Python")


class StaticInterviewContextService:
    """Small composed-context fixture for decision policy tests."""

    def __init__(self, context: InterviewContext | None) -> None:
        self._context = context

    def build(self, application_id: int) -> InterviewContext | None:
        return self._context if application_id == 1 else None


def _context(
    *,
    score: float | None = 80.0,
    gaps: GapContext | None = _DEFAULT_GAPS,
    recommendations: tuple[str, ...] = ("Highlight Python experience.",),
    resume: ResumeContext | None = _DEFAULT_RESUME,
    competencies: tuple[str, ...] = ("Python",),
) -> InterviewContext:
    """Build a minimal immutable composition result with explicit evidence."""
    return InterviewContext(
        application=ApplicationContext(1, 2, 3, "draft"),
        vacancy=VacancyContext(2, "Backend Engineer", competencies),
        company=CompanyContext(3, "ACD"),
        resume=resume,
        identified_competencies=competencies,
        ats_result=None if score is None else ATSContext(score, recommendations),
        gaps=gaps,
    )


def _service(context: InterviewContext | None) -> CandidateDecisionService:
    return CandidateDecisionService(StaticInterviewContextService(context))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("score", "gaps", "expected"),
    [
        (85.0, GapContext(("Docker",)), CandidateDecision.STRONG_APPLY),
        (72.0, GapContext(("Docker", "Kubernetes")), CandidateDecision.APPLY),
        (60.0, GapContext(("Docker", "Kubernetes", "AWS", "Terraform")), CandidateDecision.REVIEW),
        (45.0, GapContext(("Docker",)), CandidateDecision.LOW_PRIORITY),
    ],
)
def test_candidate_decision_policy_uses_persisted_ats_and_gaps(
    score: float,
    gaps: GapContext,
    expected: CandidateDecision,
) -> None:
    """Known evidence maps deterministically to the documented policy states."""
    result = _service(_context(score=score, gaps=gaps)).assess(1)

    assert result.decision is expected
    assert result.score == score
    assert result.confidence is DecisionConfidence.HIGH
    assert result.gaps == gaps.missing_skills
    assert result.recommendations == ("Highlight Python experience.",)


def test_candidate_decision_requires_composed_evidence_without_penalizing_candidate() -> None:
    """Absent application, ATS, resume, or vacancy evidence is insufficient data."""
    missing_application = _service(None).assess(1)
    missing_ats = _service(_context(score=None)).assess(1)
    missing_resume = _service(_context(resume=None)).assess(1)
    missing_competencies = _service(_context(competencies=())).assess(1)

    for result in (missing_application, missing_ats, missing_resume, missing_competencies):
        assert result.decision is CandidateDecision.INSUFFICIENT_DATA
        assert result.confidence is DecisionConfidence.LOW
        assert result.reasons

    assert missing_ats.score is None
    assert "persisted ATS result" in missing_ats.reasons[0]


def test_candidate_decision_treats_missing_gaps_as_unknown_not_as_a_strength() -> None:
    """A high ATS score cannot produce strong apply without persisted gap evidence."""
    result = _service(_context(score=82.0, gaps=None)).assess(1)

    assert result.decision is CandidateDecision.REVIEW
    assert result.confidence is DecisionConfidence.MEDIUM
    assert result.gaps == ()
    assert "Persisted gap analysis is unavailable." in result.risks


def test_candidate_decision_preserves_empty_recommendations_and_is_explainable() -> None:
    """No recommendation is invented when the persisted ATS result has none."""
    result = _service(_context(score=82.0, gaps=GapContext(), recommendations=())).assess(1)

    assert result.recommendations == ()
    assert result.decision is CandidateDecision.STRONG_APPLY
    assert result.strengths
    assert result.reasons == (
        "Persisted ATS score: 82.00.",
        "Persisted missing skills: 0.",
        "Decision policy outcome: strong_apply.",
    )


def test_candidate_decision_result_is_immutable_and_serializable() -> None:
    """Decision output is safe for future Presentation and agent consumers."""
    result = _service(_context()).assess(1)

    with pytest.raises(FrozenInstanceError):
        result.score = 10.0  # type: ignore[misc]
    assert isinstance(result, CandidateDecisionResult)
    json.dumps(asdict(result))


def test_candidate_decision_service_has_no_infrastructure_dependency() -> None:
    """Decision policy remains an Application concern independent from persistence."""
    source = inspect.getsource(CandidateDecisionService)

    assert "acd.infrastructure" not in source
