"""Infrastructure adapter for vacancy read queries."""

from __future__ import annotations

from acd.application.query_ports import VacancyQueryDTO, VacancyQueryPort
from acd.infrastructure.repositories.job_profile_repository import JobProfileRepository
from acd.infrastructure.repositories.job_repository import JobRepository


class VacancyQueryAdapter(VacancyQueryPort):
    """Maps vacancy and structured profile repository reads to Application DTOs."""

    def __init__(
        self,
        job_repository: JobRepository,
        job_profile_repository: JobProfileRepository,
    ) -> None:
        self._job_repository = job_repository
        self._job_profile_repository = job_profile_repository

    def get_by_id(self, job_id: int) -> VacancyQueryDTO | None:
        """Return a vacancy DTO with available requirements and competencies."""
        job = self._job_repository.get_by_id(job_id)
        if job is None:
            return None
        profile = self._job_profile_repository.get_by_job(job_id)
        competencies = () if profile is None else self._split_competencies(profile.skills)
        requirements = "" if profile is None else profile.raw_description
        return VacancyQueryDTO(
            job_id=job.id,
            title=job.title,
            company_id=job.company_id,
            notes=job.notes,
            requirements=requirements,
            competencies=competencies,
        )

    @staticmethod
    def _split_competencies(value: str) -> tuple[str, ...]:
        """Map the repository's comma-separated representation to a DTO sequence."""
        return tuple(item.strip() for item in value.split(",") if item.strip())
