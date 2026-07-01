from __future__ import annotations

from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job_profile import JobProfile
from acd.services.ai_generation_service import ResumeGenerationService


def generate_resume(service: ResumeGenerationService, *, curriculum: Curriculum, job_profile: JobProfile, language: str) -> dict[str, object]:
    """Aplicação para gerar uma nova versão de currículo."""
    return service.generate_resume(curriculum=curriculum, job_profile=job_profile, language=language)
