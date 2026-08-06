"""Presentation boundary for Candidate Decision Support."""

from __future__ import annotations

from acd.application.candidate_decision_service import CandidateDecision, CandidateDecisionResult
from acd.application.candidate_decision_use_case import CandidateDecisionUseCase
from acd.presentation.models.candidate_decision_view_state import CandidateDecisionViewState


class CandidateDecisionViewModel:
    """Map the Application decision contract to a stable UI-facing state."""

    _PRESENTATION = {
        CandidateDecision.STRONG_APPLY: ("Strong application", "The application has strong persisted evidence."),
        CandidateDecision.APPLY: ("Apply", "The application has sufficient persisted evidence."),
        CandidateDecision.REVIEW: ("Review application", "Review the available evidence before proceeding."),
        CandidateDecision.LOW_PRIORITY: ("Low priority", "The persisted evidence indicates low priority."),
        CandidateDecision.INSUFFICIENT_DATA: ("Insufficient data", "More persisted evidence is required for a decision."),
    }

    def __init__(self, candidate_decision_use_case: CandidateDecisionUseCase) -> None:
        self._candidate_decision_use_case = candidate_decision_use_case

    def load(self, application_id: int) -> CandidateDecisionViewState:
        """Return the current UI-facing decision state for an application."""
        return self._to_view_state(self._candidate_decision_use_case.execute(application_id))

    def _to_view_state(self, result: CandidateDecisionResult) -> CandidateDecisionViewState:
        headline, summary = self._PRESENTATION[result.decision]
        return CandidateDecisionViewState(
            decision=result.decision.value,
            score=result.score,
            confidence=result.confidence.value,
            headline=headline,
            summary=summary,
            reasons=result.reasons,
            strengths=result.strengths,
            risks=result.risks,
            gaps=result.gaps,
            recommendations=result.recommendations,
        )
