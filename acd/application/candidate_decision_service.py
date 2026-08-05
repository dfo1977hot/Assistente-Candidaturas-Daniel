"""Deterministic decision support for an existing application."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from acd.application.composition.interview_context_service import InterviewContextService
from acd.application.composition.read_models import InterviewContext


class CandidateDecision(StrEnum):
    """Actions recommended from persisted candidate-application evidence."""

    STRONG_APPLY = "strong_apply"
    APPLY = "apply"
    REVIEW = "review"
    LOW_PRIORITY = "low_priority"
    INSUFFICIENT_DATA = "insufficient_data"


class DecisionConfidence(StrEnum):
    """Confidence derived from the completeness of persisted evidence."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class CandidateDecisionResult:
    """Serializable, read-only recommendation for one application."""

    application_id: int
    decision: CandidateDecision
    score: float | None
    confidence: DecisionConfidence
    strengths: tuple[str, ...]
    risks: tuple[str, ...]
    gaps: tuple[str, ...]
    recommendations: tuple[str, ...]
    reasons: tuple[str, ...]


class CandidateDecisionService:
    """Derive a transparent application decision from existing read models."""

    _STRONG_APPLY_SCORE = 80.0
    _APPLY_SCORE = 65.0
    _LOW_PRIORITY_SCORE = 50.0
    _STRONG_APPLY_MAX_GAPS = 1
    _APPLY_MAX_GAPS = 3
    _LOW_PRIORITY_MIN_GAPS = 6

    def __init__(self, interview_context_service: InterviewContextService) -> None:
        self._interview_context_service = interview_context_service

    def assess(self, application_id: int) -> CandidateDecisionResult:
        """Assess an application using only persisted, composed information."""
        context = self._interview_context_service.build(application_id)
        if not self._has_required_evidence(context):
            return self._insufficient_data_result(application_id, context)

        assert context is not None
        assert context.ats_result is not None
        score = round(context.ats_result.total_score, 2)
        gaps_known = context.gaps is not None
        gaps = () if context.gaps is None else context.gaps.missing_skills
        decision = self._decide(score, len(gaps), gaps_known)
        confidence = DecisionConfidence.HIGH if gaps_known else DecisionConfidence.MEDIUM
        strengths = self._strengths(score, context)
        risks = self._risks(score, gaps, gaps_known)
        reasons = self._reasons(decision, score, gaps, gaps_known)
        return CandidateDecisionResult(
            application_id=application_id,
            decision=decision,
            score=score,
            confidence=confidence,
            strengths=strengths,
            risks=risks,
            gaps=gaps,
            recommendations=context.ats_result.recommendations,
            reasons=reasons,
        )

    @staticmethod
    def _has_required_evidence(context: InterviewContext | None) -> bool:
        return bool(
            context is not None
            and context.resume is not None
            and context.ats_result is not None
            and context.vacancy.competencies
        )

    def _insufficient_data_result(
        self,
        application_id: int,
        context: InterviewContext | None,
    ) -> CandidateDecisionResult:
        missing = self._missing_evidence(context)
        recommendations = () if context is None or context.ats_result is None else context.ats_result.recommendations
        return CandidateDecisionResult(
            application_id=application_id,
            decision=CandidateDecision.INSUFFICIENT_DATA,
            score=None if context is None or context.ats_result is None else round(context.ats_result.total_score, 2),
            confidence=DecisionConfidence.LOW,
            strengths=(),
            risks=tuple(f"Missing required evidence: {item}." for item in missing),
            gaps=(),
            recommendations=recommendations,
            reasons=tuple(f"Decision support requires {item}." for item in missing),
        )

    @staticmethod
    def _missing_evidence(context: InterviewContext | None) -> tuple[str, ...]:
        if context is None:
            return ("application context",)
        missing: list[str] = []
        if context.resume is None:
            missing.append("resume")
        if context.ats_result is None:
            missing.append("persisted ATS result")
        if not context.vacancy.competencies:
            missing.append("vacancy competencies")
        return tuple(missing)

    def _decide(
        self,
        score: float,
        gap_count: int,
        gaps_known: bool,
    ) -> CandidateDecision:
        if score < self._LOW_PRIORITY_SCORE or gap_count >= self._LOW_PRIORITY_MIN_GAPS:
            return CandidateDecision.LOW_PRIORITY
        if not gaps_known:
            return CandidateDecision.REVIEW
        if score >= self._STRONG_APPLY_SCORE and gap_count <= self._STRONG_APPLY_MAX_GAPS:
            return CandidateDecision.STRONG_APPLY
        if score >= self._APPLY_SCORE and gap_count <= self._APPLY_MAX_GAPS:
            return CandidateDecision.APPLY
        return CandidateDecision.REVIEW

    def _strengths(self, score: float, context: InterviewContext) -> tuple[str, ...]:
        strengths: list[str] = []
        if score >= self._APPLY_SCORE:
            strengths.append(f"Persisted ATS score is {score:.2f}.")
        if context.gaps is not None and not context.gaps.missing_skills:
            strengths.append("Persisted gap analysis reports no missing skills.")
        return tuple(strengths)

    def _risks(
        self,
        score: float,
        gaps: tuple[str, ...],
        gaps_known: bool,
    ) -> tuple[str, ...]:
        risks = [f"Missing skill: {gap}." for gap in gaps]
        if score < self._LOW_PRIORITY_SCORE:
            risks.append(f"Persisted ATS score is below {self._LOW_PRIORITY_SCORE:.0f}.")
        if not gaps_known:
            risks.append("Persisted gap analysis is unavailable.")
        return tuple(risks)

    def _reasons(
        self,
        decision: CandidateDecision,
        score: float,
        gaps: tuple[str, ...],
        gaps_known: bool,
    ) -> tuple[str, ...]:
        reasons = [f"Persisted ATS score: {score:.2f}."]
        if gaps_known:
            reasons.append(f"Persisted missing skills: {len(gaps)}.")
        else:
            reasons.append("No persisted gap analysis is available.")
        reasons.append(f"Decision policy outcome: {decision.value}.")
        return tuple(reasons)
