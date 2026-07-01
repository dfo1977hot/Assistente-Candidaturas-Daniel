from __future__ import annotations

from typing import Optional

from acd.core.logger import logger
from acd.domain.entities.job import Job
from acd.infrastructure.repositories.job_repository import JobRepository


class JobService:
    """Camada de serviço para regras de negócio das vagas."""

    def __init__(self, repository: Optional[JobRepository] = None) -> None:
        self.repository = repository or JobRepository()

    def create_job(
        self,
        *,
        company_id: int,
        title: str,
        location: str = "",
        work_model: str = "",
        employment_type: str = "",
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        currency: str = "",
        status: str = "Nova",
        source: str = "",
        job_url: str = "",
        recruiter: str = "",
        application_deadline: Optional[str] = None,
        application_date: Optional[str] = None,
        priority: int = 0,
        notes: str = "",
    ) -> Job:
        """Valida e cria uma vaga."""
        self._validate_required_fields(company_id=company_id, title=title)
        job = Job(
            company_id=company_id,
            title=title.strip(),
            location=location.strip(),
            work_model=work_model.strip(),
            employment_type=employment_type.strip(),
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency.strip(),
            status=status.strip() or "Nova",
            source=source.strip(),
            job_url=job_url.strip(),
            recruiter=recruiter.strip(),
            application_deadline=self._parse_optional_date(application_deadline),
            application_date=self._parse_optional_date(application_date),
            priority=priority,
            notes=notes.strip(),
        )
        created = self.repository.create(job)
        logger.info("Nova vaga criada: %s", created.title)
        return created

    def update_job(
        self,
        job_id: int,
        *,
        company_id: int,
        title: str,
        location: str = "",
        work_model: str = "",
        employment_type: str = "",
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        currency: str = "",
        status: str = "Nova",
        source: str = "",
        job_url: str = "",
        recruiter: str = "",
        application_deadline: Optional[str] = None,
        application_date: Optional[str] = None,
        priority: int = 0,
        notes: str = "",
    ) -> Optional[Job]:
        """Atualiza uma vaga existente."""
        self._validate_required_fields(company_id=company_id, title=title)
        job = self.repository.get_by_id(job_id)
        if job is None:
            return None

        job.company_id = company_id
        job.title = title.strip()
        job.location = location.strip()
        job.work_model = work_model.strip()
        job.employment_type = employment_type.strip()
        job.salary_min = salary_min
        job.salary_max = salary_max
        job.currency = currency.strip()
        job.status = status.strip() or "Nova"
        job.source = source.strip()
        job.job_url = job_url.strip()
        job.recruiter = recruiter.strip()
        job.application_deadline = self._parse_optional_date(application_deadline)
        job.application_date = self._parse_optional_date(application_date)
        job.priority = priority
        job.notes = notes.strip()
        updated = self.repository.update(job)
        logger.info("Vaga atualizada: %s", updated.title)
        return updated

    def delete_job(self, job_id: int) -> bool:
        """Remove uma vaga."""
        deleted = self.repository.delete(job_id)
        if deleted:
            logger.info("Vaga removida: %s", job_id)
        return deleted

    def list_jobs(self) -> list[Job]:
        """Retorna todas as vagas."""
        return self.repository.get_all()

    def search_jobs(self, query: str) -> list[Job]:
        """Busca vagas por cargo."""
        return self.repository.search(query)

    def filter_jobs(self, *, company_id: Optional[int] = None, status: Optional[str] = None, work_model: Optional[str] = None, employment_type: Optional[str] = None) -> list[Job]:
        """Filtra vagas por empresa, status e modalidade."""
        return self.repository.filter(
            company_id=company_id,
            status=status,
            work_model=work_model,
            employment_type=employment_type,
        )

    def count_jobs(self) -> int:
        """Retorna o total de vagas."""
        return self.repository.count()

    def _validate_required_fields(self, *, company_id: int, title: str) -> None:
        if company_id <= 0:
            raise ValueError("Empresa é obrigatória.")
        if not title or not title.strip():
            raise ValueError("Cargo é obrigatório.")

    def _parse_optional_date(self, value: Optional[str]) -> Optional[object]:
        if not value:
            return None
        from datetime import date

        return date.fromisoformat(value)
