"""Immutable Presentation contract for Candidate Decision Support."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateDecisionViewState:
    """UI-ready projection of a candidate decision without business behavior."""

    decision: str
    score: float | None
    confidence: str
    headline: str
    summary: str
    reasons: tuple[str, ...]
    strengths: tuple[str, ...]
    risks: tuple[str, ...]
    gaps: tuple[str, ...]
    recommendations: tuple[str, ...]
