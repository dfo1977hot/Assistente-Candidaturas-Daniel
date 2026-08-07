from __future__ import annotations

from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job_profile import JobProfile
from acd.services.ai_generation_service import CoverLetterGenerationService


def generate_cover_letter(
    service: CoverLetterGenerationService,
    *,
    curriculum: Curriculum,
    job_profile: JobProfile,
    language: str,
) -> dict[str, object]:
    """Aplicação para gerar uma nova carta de apresentação."""
    return service.generate_cover_letter(
        curriculum=curriculum, job_profile=job_profile, language=language
    )
