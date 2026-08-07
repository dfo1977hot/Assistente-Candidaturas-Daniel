from __future__ import annotations

from acd.application.resume_optimization.resume_analysis_orchestrator import (
    ResumeAnalysisOrchestrator,
)
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job_profile import JobProfile
from acd.domain.planner.recommendation import Recommendation


class FakeATSService:
    """Deterministic ATS capability for orchestration tests."""

    def compare_curriculum(
        self, *, curriculum: Curriculum, job_profile: JobProfile
    ) -> dict[str, object]:
        return {
            "total_score": 72.0,
            "gaps": {"missing_skills": ["Python"], "desired_skills": ["Docker"]},
            "recommendations": ["Adicionar Python no currículo."],
        }


class FakeRecommendationEngine:
    """Deterministic strategic recommendation capability."""

    def generate(self, overall_score: float) -> list[Recommendation]:
        assert overall_score == 72.0
        return [Recommendation(title="Adaptar currículo", description="Priorizar aderência.")]


def test_resume_analysis_orchestrator_composes_existing_capabilities() -> None:
    """The Studio analysis aggregates ATS gaps and strategic recommendations."""
    orchestrator = ResumeAnalysisOrchestrator(FakeATSService(), FakeRecommendationEngine())

    result = orchestrator.analyze(
        curriculum=Curriculum(id=1, name="Base", version="v1.0", description="SQL"),
        job_profile=JobProfile(id=1, job_id=1, raw_description="Backend"),
    )

    assert result.ats_score == 72.0
    assert result.gaps["missing_skills"] == ["Python"]
    assert result.proposed_improvements == (
        "Adicionar Python no currículo.",
        "Priorizar aderência.",
    )
