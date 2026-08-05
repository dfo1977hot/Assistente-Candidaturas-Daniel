"""Application entry point for Candidate Decision Support."""

from __future__ import annotations

from acd.application.candidate_decision_service import (
    CandidateDecisionResult,
    CandidateDecisionService,
)


class CandidateDecisionUseCase:
    """Expose one reusable operation for assessing an existing application."""

    def __init__(self, candidate_decision_service: CandidateDecisionService) -> None:
        self._candidate_decision_service = candidate_decision_service

    def execute(self, application_id: int) -> CandidateDecisionResult:
        """Return the current deterministic decision for an application."""
        return self._candidate_decision_service.assess(application_id)
