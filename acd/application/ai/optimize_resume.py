from __future__ import annotations

from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job_profile import JobProfile
from acd.services.ai_generation_service import ResumeGenerationService


def optimize_resume(
    service: ResumeGenerationService,
    *,
    curriculum: Curriculum,
    job_profile: JobProfile,
    language: str,
) -> dict[str, object]:
    """Aplicação para otimizar um currículo com IA."""
    return service.generate_resume(
        curriculum=curriculum, job_profile=job_profile, language=language
    )
