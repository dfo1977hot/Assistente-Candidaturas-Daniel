from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any
from urllib.parse import urlparse

from acd.core.logger import logger
from acd.domain.entities.job import Job
from acd.infrastructure.repositories.job_repository import JobRepository


class JobService:
    """Camada de serviço responsável pelas regras de negócio das vagas."""

    JOB_STATUSES = (
        "Nova",
        "Analisada",
        "Currículo Enviado",
        "Carta Enviada",
        "Inscrição Concluída",
        "Triagem RH",
        "Entrevista RH",
        "Entrevista Técnica",
        "Teste",
        "Oferta",
        "Rejeitada",
        "Encerrada",
    )
    VALID_STATUS = frozenset(JOB_STATUSES)

    def __init__(
        self,
        repository: JobRepository | None = None,
        event_dispatcher: Callable[[str, dict[str, Any]], object] | None = None,
    ) -> None:
        self.repository = repository or JobRepository()
        self._event_dispatcher = event_dispatcher

    def set_event_dispatcher(
        self, dispatcher: Callable[[str, dict[str, Any]], object] | None
    ) -> None:
        self._event_dispatcher = dispatcher

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
        application_url: str = "",
        recruiter: str = "",
        recruiter_email: str = "",
        application_deadline: str | None = None,
        application_date: str | None = None,
        priority: int = 0,
        notes: str = "",
        imported: bool = False,
    ) -> Job:
        """Valida e cria uma nova vaga."""

        self._validate_required_fields(company_id=company_id, title=title)
        self._validate_salary_range(salary_min, salary_max)
        self._validate_status(status)
        self._validate_url(job_url, field_name="URL da vaga")
        self._validate_url(application_url, field_name="URL da candidatura")
        if job_url.strip() and self.repository.url_exists(job_url):
            raise ValueError("Esta URL já está cadastrada em outra vaga.")

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
            application_url=application_url.strip(),
            recruiter=recruiter.strip(),
            recruiter_email=recruiter_email.strip(),
            application_deadline=self._parse_optional_date(application_deadline),
            application_date=self._parse_optional_date(application_date),
            priority=priority,
            notes=notes.strip(),
        )

        created = self.repository.create(job)

        if self._event_dispatcher is not None:
            event_type = "job.imported" if imported else "job.created"
            self._event_dispatcher(
                event_type,
                {
                    "entity_id": created.id,
                    "job_id": created.id,
                    "company_id": created.company_id,
                    "occurrence_id": f"job:{created.id}:created",
                },
            )

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
        application_url: str = "",
        recruiter: str = "",
        recruiter_email: str = "",
        application_deadline: str | None = None,
        application_date: str | None = None,
        priority: int = 0,
        notes: str = "",
    ) -> Job | None:
        """Atualiza uma vaga existente."""

        self._validate_required_fields(company_id=company_id, title=title)
        self._validate_salary_range(salary_min, salary_max)
        self._validate_status(status)
        self._validate_url(job_url, field_name="URL da vaga")
        self._validate_url(application_url, field_name="URL da candidatura")
        if job_url.strip() and self.repository.url_exists(
            job_url,
            exclude_job_id=job_id,
        ):
            raise ValueError("Esta URL já está cadastrada em outra vaga.")

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
        job.application_url = application_url.strip()
        job.recruiter = recruiter.strip()
        job.recruiter_email = recruiter_email.strip()
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

    def delete_job(self, job_id: int, *, delete_linked: bool = False) -> bool:
        """Remove uma vaga."""

        deleted = self.repository.delete(job_id, delete_linked=delete_linked)

        if deleted:
            logger.info("DELETE_JOB | id=%s", job_id)

        return deleted

    def get_job(self, job_id: int) -> Job | None:
        """Retorna uma vaga pelo ID."""
        return self.repository.get_by_id(job_id)

    def get_job_by_url(self, job_url: str) -> Job | None:
        """Retorna uma vaga pelo endereço da publicação."""
        return self.repository.get_by_url(job_url)

    def get_job_by_linkedin_job_id(self, linkedin_job_id: str) -> Job | None:
        """Retorna uma vaga pelo identificador numérico do LinkedIn."""
        return self.repository.get_by_linkedin_job_id(linkedin_job_id)

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

    def job_url_exists(
        self,
        job_url: str,
        *,
        exclude_job_id: int | None = None,
    ) -> bool:
        """Informa se uma URL já está cadastrada."""
        return self.repository.url_exists(
            job_url,
            exclude_job_id=exclude_job_id,
        )

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

        for value, label in (
            (salary_min, "Remuneração oferecida"),
            (salary_max, "Remuneração ideal"),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{label} não pode ser negativa.")

    def _validate_status(self, status: str) -> None:
        """Valida o status informado."""

        status = status.strip() or "Nova"

        if status not in self.VALID_STATUS:
            raise ValueError(f"Status inválido: '{status}'.")

    @staticmethod
    def _validate_url(url: str, *, field_name: str = "URL") -> None:
        """Valida uma URL opcional de vaga ou candidatura."""

        normalized = url.strip()
        if not normalized:
            return

        parsed = urlparse(normalized)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"{field_name} deve iniciar com http:// ou https://.")

    @staticmethod
    def _parse_optional_date(value: str | None) -> date | None:
        """Converte uma data ISO para datetime.date."""

        if not value:
            return None

        return date.fromisoformat(value)
