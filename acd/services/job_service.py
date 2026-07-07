from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

from acd.core.logger import logger
from acd.domain.entities.job import Job
from acd.infrastructure.repositories.job_repository import JobRepository


class JobService:
    """Camada de serviço responsável pelas regras de negócio das vagas."""

    VALID_STATUS = {
        "Nova",
        "Currículo enviado",
        "Triagem",
        "Entrevista RH",
        "Entrevista Técnica",
        "Proposta",
        "Contratado",
        "Rejeitado",
        "Encerrada",
    }

    def __init__(self, repository: JobRepository | None = None) -> None:
        self.repository = repository or JobRepository()

    def create_job(
        self,
        *,
        company_id: int,
        title: str,
        location: str = "",
        work_model: str = "",
        employment_type: str = "",
        salary_min: float | None = None,
        salary_max: float | None = None,
        currency: str = "",
        status: str = "Nova",
        source: str = "",
        job_url: str = "",
        recruiter: str = "",
        application_deadline: str | None = None,
        application_date: str | None = None,
        priority: int = 0,
        notes: str = "",
    ) -> Job:
        """Valida e cria uma nova vaga."""

        self._validate_required_fields(company_id=company_id, title=title)
        self._validate_salary_range(salary_min, salary_max)
        self._validate_status(status)
        self._validate_url(job_url)

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

        logger.info(
            "CREATE_JOB | id=%s | company=%s | title=%s",
            created.id,
            created.company_id,
            created.title,
        )

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
        salary_min: float | None = None,
        salary_max: float | None = None,
        currency: str = "",
        status: str = "Nova",
        source: str = "",
        job_url: str = "",
        recruiter: str = "",
        application_deadline: str | None = None,
        application_date: str | None = None,
        priority: int = 0,
        notes: str = "",
    ) -> Job | None:
        """Atualiza uma vaga existente."""

        self._validate_required_fields(company_id=company_id, title=title)
        self._validate_salary_range(salary_min, salary_max)
        self._validate_status(status)
        self._validate_url(job_url)

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

        logger.info(
            "UPDATE_JOB | id=%s | company=%s | title=%s",
            updated.id,
            updated.company_id,
            updated.title,
        )

        return updated

    def delete_job(self, job_id: int) -> bool:
        """Remove uma vaga."""

        deleted = self.repository.delete(job_id)

        if deleted:
            logger.info("DELETE_JOB | id=%s", job_id)

        return deleted

    def get_job(self, job_id: int) -> Job | None:
        """Retorna uma vaga pelo ID."""
        return self.repository.get_by_id(job_id)

    def list_jobs(self) -> list[Job]:
        """Retorna todas as vagas cadastradas."""
        return self.repository.get_all()

    def search_jobs(self, query: str) -> list[Job]:
        """Pesquisa vagas."""
        return self.repository.search(query)

    def filter_jobs(
        self,
        *,
        company_id: int | None = None,
        status: str | None = None,
        work_model: str | None = None,
        employment_type: str | None = None,
    ) -> list[Job]:
        """Filtra vagas."""

        return self.repository.filter(
            company_id=company_id,
            status=status,
            work_model=work_model,
            employment_type=employment_type,
        )

    def count_jobs(self) -> int:
        """Retorna o número de vagas cadastradas."""
        return self.repository.count()

    @staticmethod
    def _validate_required_fields(*, company_id: int, title: str) -> None:
        """Valida os campos obrigatórios."""

        if company_id <= 0:
            raise ValueError("Empresa é obrigatória.")

        if not title or not title.strip():
            raise ValueError("Cargo é obrigatório.")

    @staticmethod
    def _validate_salary_range(
        salary_min: float | None,
        salary_max: float | None,
    ) -> None:
        """Valida a faixa salarial."""

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise ValueError("O salário mínimo não pode ser maior que o salário máximo.")

    def _validate_status(self, status: str) -> None:
        """Valida o status informado."""

        status = status.strip() or "Nova"

        if status not in self.VALID_STATUS:
            raise ValueError(f"Status inválido: '{status}'.")

    @staticmethod
    def _validate_url(url: str) -> None:
        """Valida a URL da vaga."""

        if not url:
            return

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError("A URL da vaga deve iniciar com http:// ou https://.")

    @staticmethod
    def _parse_optional_date(value: str | None) -> date | None:
        """Converte uma data ISO para datetime.date."""

        if not value:
            return None

        return date.fromisoformat(value)
