"""Presentation-safe state for a transient optimized resume evaluation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizedResumeEvaluationViewState:
    """Immutable projection rendered by the resume version review panel."""

    status: str
    title: str
    message: str
    application_id: int
    resume_version_id: int | None = None
    original_score: float | None = None
    optimized_score: float | None = None
    score_delta: float | None = None
    comparison_state: str = "unknown"
    original_gaps: tuple[str, ...] = ()
    optimized_gaps: tuple[str, ...] = ()
    original_recommendations: tuple[str, ...] = ()
    optimized_recommendations: tuple[str, ...] = ()
    persisted: bool = False
