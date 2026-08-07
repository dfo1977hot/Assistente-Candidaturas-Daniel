from __future__ import annotations

from acd.services.ats_service import ATSService


def generate_recommendations(
    service: ATSService,
    *,
    missing_skills: list[str],
    desired_skills: list[str],
    curriculum_strengths: list[str],
) -> list[str]:
    """Aplicação para gerar recomendações a partir das lacunas."""
    return service.recommendation_strategy.generate(
        missing_skills=missing_skills,
        desired_skills=desired_skills,
        curriculum_strengths=curriculum_strengths,
    )
