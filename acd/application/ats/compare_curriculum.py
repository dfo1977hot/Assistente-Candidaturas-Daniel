from __future__ import annotations

from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job_profile import JobProfile
from acd.services.ats_service import ATSService


def compare_curriculum(service: ATSService, *, curriculum: Curriculum, job_profile: JobProfile) -> dict[str, object]:
    """Aplicação para comparar currículo e vaga."""
    return service.compare_curriculum(curriculum=curriculum, job_profile=job_profile)
