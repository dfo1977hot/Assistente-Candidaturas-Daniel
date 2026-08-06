"""Application orchestration for resume optimization analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from acd.application.ats.compare_curriculum import compare_curriculum
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job_profile import JobProfile
from acd.domain.planner.recommendation import Recommendation


class ATSComparisonService(Protocol):
    """Provides the existing ATS comparison capability."""

    def compare_curriculum(
        self, *, curriculum: Curriculum, job_profile: JobProfile
    ) -> dict[str, object]:
        """Compare a curriculum with a job profile."""


class ScoreRecommendationEngine(Protocol):
    """Generates strategic recommendations from an overall score."""

    def generate(self, overall_score: float) -> list[Recommendation]:
        """Generate recommendations for a score."""


@dataclass(frozen=True)
class ResumeOptimizationAnalysis:
    """Read-only analysis produced before any resume change is approved."""

    ats_score: float
    gaps: dict[str, list[str]]
    ats_recommendations: tuple[str, ...]
    strategic_recommendations: tuple[Recommendation, ...]
    proposed_improvements: tuple[str, ...]


class ResumeAnalysisOrchestrator:
    """Composes existing ATS and recommendation capabilities for the Studio."""

    def __init__(
        self,
        ats_service: ATSComparisonService,
        recommendation_engine: ScoreRecommendationEngine,
    ) -> None:
        self._ats_service = ats_service
        self._recommendation_engine = recommendation_engine

    def analyze(
        self, *, curriculum: Curriculum, job_profile: JobProfile
    ) -> ResumeOptimizationAnalysis:
        """Produce a non-mutating optimization proposal for a selected pair."""
        ats_result = compare_curriculum(
            self._ats_service, curriculum=curriculum, job_profile=job_profile
        )
        ats_score = float(ats_result["total_score"])
        gaps = dict(ats_result["gaps"])
        ats_recommendations = tuple(ats_result["recommendations"])
        strategic_recommendations = tuple(self._recommendation_engine.generate(ats_score))
        proposed_improvements = tuple(
            dict.fromkeys(
                (*ats_recommendations, *(item.description for item in strategic_recommendations))
            )
        )
        return ResumeOptimizationAnalysis(
            ats_score=ats_score,
            gaps=gaps,
            ats_recommendations=ats_recommendations,
            strategic_recommendations=strategic_recommendations,
            proposed_improvements=proposed_improvements,
        )
