"""Batch import of authenticated LinkedIn saved jobs."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import re
import unicodedata

from acd.infrastructure.linkedin.linkedin_saved_jobs_browser import (
    LinkedInSavedJobsBrowser,
    LinkedInSavedJobsBrowserError,
    SavedLinkedInJob,
)
from acd.infrastructure.repositories.job_repository import JobRepository
from acd.services.closed_linkedin_jobs_registry import ClosedLinkedInJobsRegistry
from acd.services.company_service import CompanyService
from acd.services.job_service import JobService
from acd.services.linkedin_job_import_service import (
    ImportedLinkedInJob,
    LinkedInJobImportService,
)
from acd.services.recruiter_email_research_service import (
    RecruiterEmailResearchRequest,
    RecruiterEmailResearchService,
)
from acd.services.salary_research_service import (
    SalaryResearchRequest,
    SalaryResearchService,
)


@dataclass(frozen=True, slots=True)
class SavedJobsProgress:
    """Progress snapshot sent to Presentation."""

    stage: str
    message: str
    current: int = 0
    total: int = 0
    title: str = ""
    company_name: str = ""
    imported: int = 0
    existing: int = 0
    failed: int = 0
    companies_created: int = 0
    deleted: int = 0


@dataclass(frozen=True, slots=True)
class SavedJobsImportResult:
    """Final summary of one saved-jobs import."""

    found: int
    imported: int
    existing: int
    failed: int
    companies_created: int
    deleted: int = 0
    errors: tuple[str, ...] = ()




@dataclass(frozen=True, slots=True)
class _PendingImport:
    current: int
    reference: SavedLinkedInJob
    job: ImportedLinkedInJob


class LinkedInSavedJobsImportService:
    """Coordinate browser collection, enrichment, company creation, and persistence."""

    def __init__(
        self,
        browser: LinkedInSavedJobsBrowser,
        job_import_service: LinkedInJobImportService,
        job_service: JobService,
        company_service: CompanyService,
        job_repository: JobRepository | None = None,
        salary_research_service: SalaryResearchService | None = None,
        recruiter_email_research_service: RecruiterEmailResearchService | None = None,
        closed_jobs_registry: ClosedLinkedInJobsRegistry | None = None,
    ) -> None:
        self._browser = browser
        self._job_import_service = job_import_service
        self._job_service = job_service
        self._company_service = company_service
        self._job_repository = job_repository
        self._salary_research_service = salary_research_service
        self._recruiter_email_research_service = recruiter_email_research_service
        self._closed_jobs_registry = closed_jobs_registry or ClosedLinkedInJobsRegistry()

    def import_saved_jobs(
        self,
        *,
        progress_callback: Callable[[SavedJobsProgress], None] | None = None,
        cancellation_requested: Callable[[], bool] | None = None,
    ) -> SavedJobsImportResult:
        """Importe somente vagas novas e pesquise salários ausentes em paralelo."""
        self._emit(progress_callback, SavedJobsProgress("browser", "Abrindo o LinkedIn..."))
        processed_linkedin_job_ids = self._processed_linkedin_job_ids()
        permanently_excluded_job_ids = self._closed_jobs_registry.ids()
        references = self._browser.collect_saved_jobs(
            cancellation_requested=cancellation_requested,
            status_callback=lambda message: self._emit(
                progress_callback,
                SavedJobsProgress("browser", message),
            ),
            excluded_job_ids=processed_linkedin_job_ids,
            permanently_excluded_job_ids=permanently_excluded_job_ids,
        )
        total = len(references)
        imported = existing = failed = companies_created = deleted = 0
        errors: list[str] = []
        pending: list[_PendingImport] = []

        for current, reference in enumerate(references, start=1):
            self._raise_if_cancelled(cancellation_requested)
            self._emit(
                progress_callback,
                SavedJobsProgress(
                    "importing",
                    "Coletando dados da vaga...",
                    current=current,
                    total=total,
                    title=reference.title,
                    company_name=reference.company_name,
                    imported=imported,
                    existing=existing,
                    failed=failed,
                    companies_created=companies_created,
                    deleted=deleted,
                ),
            )
            if (
                reference.application_url
                and self._same_job_and_application_url(
                    reference.url,
                    reference.application_url,
                )
            ):
                self._closed_jobs_registry.mark_closed(reference.linkedin_job_id)
                deleted += self._delete_closed_job(reference)
                continue
            if reference.accepting_applications is False:
                self._closed_jobs_registry.mark_closed(reference.linkedin_job_id)
                deleted += self._delete_closed_job(reference)
                continue
            if self._job_service.job_url_exists(reference.url):
                self._update_existing_application_url(reference)
                existing += 1
                continue
            try:
                imported_job = self._job_import_service.import_from_url(reference.url)
                if imported_job.accepting_applications is False:
                    closed_id = (
                        imported_job.linkedin_job_id or reference.linkedin_job_id
                    )
                    self._closed_jobs_registry.mark_closed(closed_id)
                    deleted += self._delete_closed_job(reference)
                    continue
                pending.append(
                    _PendingImport(
                        current=current,
                        reference=reference,
                        job=self._merge_reference(imported_job, reference),
                    )
                )
            except Exception as exc:
                failed += 1
                errors.append(f"{reference.title or reference.url}: {exc}")

        enriched = self._complete_salaries_parallel(
            pending,
            progress_callback=progress_callback,
            cancellation_requested=cancellation_requested,
        )

        for item in enriched:
            self._raise_if_cancelled(cancellation_requested)
            reference = item.reference
            imported_job = item.job
            try:
                company_id, created = self._resolve_company(imported_job)
                companies_created += int(created)
                recruiter_email = self._resolve_recruiter_email(
                    imported_job,
                    reference,
                )
                self._job_service.create_job(
                    company_id=company_id,
                    title=imported_job.title or reference.title or "Vaga do LinkedIn",
                    location=imported_job.location or reference.location,
                    work_model=imported_job.work_model or reference.work_model or "Presencial",
                    employment_type=(
                        imported_job.employment_type
                        or reference.employment_type
                        or "CLT"
                    ),
                    salary_min=imported_job.salary_min,
                    salary_max=imported_job.salary_max,
                    currency=imported_job.currency or reference.currency or "BRL",
                    status="Nova",
                    source="LinkedIn",
                    job_url=imported_job.source_url or reference.url,
                    application_url=reference.application_url,
                    recruiter=imported_job.recruiter,
                    recruiter_email=recruiter_email,
                    application_deadline=imported_job.application_deadline or None,
                    application_date=None,
                    priority=3,
                    notes=self._notes_with_benefits(
                        imported_job.notes_text(),
                        imported_job.benefits,
                    ),
                )
                imported += 1
            except Exception as exc:
                failed += 1
                errors.append(f"{reference.title or reference.url}: {exc}")

            self._emit(
                progress_callback,
                SavedJobsProgress(
                    "importing",
                    "Vaga processada.",
                    current=item.current,
                    total=total,
                    title=reference.title,
                    company_name=reference.company_name,
                    imported=imported,
                    existing=existing,
                    failed=failed,
                    companies_created=companies_created,
                    deleted=deleted,
                ),
            )

        return SavedJobsImportResult(
            found=total,
            imported=imported,
            existing=existing,
            failed=failed,
            companies_created=companies_created,
            deleted=deleted,
            errors=tuple(errors),
        )

    def _complete_salaries_parallel(
        self,
        pending: list[_PendingImport],
        *,
        progress_callback: Callable[[SavedJobsProgress], None] | None,
        cancellation_requested: Callable[[], bool] | None,
    ) -> list[_PendingImport]:
        """Complete faixas ausentes com até três pesquisas simultâneas."""
        if not pending:
            return pending
        if self._salary_research_service is None:
            return [
                _PendingImport(
                    current=item.current,
                    reference=item.reference,
                    job=self._with_remuneration_semantics(item.job),
                )
                for item in pending
            ]

        # A remuneração máxima do anúncio não representa a remuneração ideal.
        # Toda vaga nova recebe uma pesquisa de mercado para preencher salary_max.
        requires_research = list(pending)

        results_by_current = {item.current: item.job for item in pending}
        max_workers = min(3, len(requires_research))
        self._emit(
            progress_callback,
            SavedJobsProgress(
                "salary",
                f"Pesquisando salários de {len(requires_research)} vaga(s)...",
                total=len(requires_research),
            ),
        )

        with ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="acd-salary",
        ) as executor:
            future_to_item = {
                executor.submit(self._complete_salary_with_ai, item.job): item
                for item in requires_research
            }
            completed = 0
            for future in as_completed(future_to_item):
                self._raise_if_cancelled(cancellation_requested)
                item = future_to_item[future]
                try:
                    results_by_current[item.current] = future.result()
                except Exception:
                    results_by_current[item.current] = item.job
                completed += 1
                self._emit(
                    progress_callback,
                    SavedJobsProgress(
                        "salary",
                        "Faixas salariais sendo completadas...",
                        current=completed,
                        total=len(requires_research),
                        title=item.reference.title,
                        company_name=item.reference.company_name,
                    ),
                )

        return [
            _PendingImport(
                current=item.current,
                reference=item.reference,
                job=results_by_current[item.current],
            )
            for item in pending
        ]


    def _complete_salary_with_ai(
        self,
        job: ImportedLinkedInJob,
    ) -> ImportedLinkedInJob:
        """Preserve advertised remuneration and research only the ideal value."""
        prepared = self._with_remuneration_semantics(job)
        if self._salary_research_service is None:
            return prepared
        try:
            result = self._salary_research_service.research(
                SalaryResearchRequest(
                    title=job.title.strip(),
                    location=job.location.strip(),
                    work_model=job.work_model.strip() or "Presencial",
                    employment_type=job.employment_type.strip() or "CLT",
                )
            )
        except Exception:
            return prepared

        return self._clone_imported_job(
            prepared,
            salary_min=prepared.salary_min,
            salary_max=result.salary_max,
            currency=prepared.currency or result.currency,
        )

    @classmethod
    def _with_remuneration_semantics(
        cls,
        job: ImportedLinkedInJob,
    ) -> ImportedLinkedInJob:
        advertised = [
            value for value in (job.salary_min, job.salary_max) if value is not None
        ]
        offered = max(advertised) if advertised else None
        return cls._clone_imported_job(
            job,
            salary_min=offered,
            salary_max=None,
            currency=job.currency or "BRL",
        )

    @staticmethod
    def _clone_imported_job(
        job: ImportedLinkedInJob,
        *,
        salary_min: float | None,
        salary_max: float | None,
        currency: str,
    ) -> ImportedLinkedInJob:
        return ImportedLinkedInJob(
            title=job.title,
            company_name=job.company_name,
            location=job.location,
            work_model=job.work_model,
            employment_type=job.employment_type or "CLT",
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            recruiter=job.recruiter,
            published_at=job.published_at,
            application_deadline=job.application_deadline,
            description=job.description,
            requirements=job.requirements,
            responsibilities=job.responsibilities,
            benefits=job.benefits,
            source_url=job.source_url,
            linkedin_job_id=job.linkedin_job_id,
            confidence=job.confidence,
            source_references=job.source_references,
            accepting_applications=job.accepting_applications,
        )

    @staticmethod
    def _benefits_text(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (list, tuple, set)):
            return "\n".join(str(item).strip() for item in value if str(item).strip())
        return str(value).strip()

    @classmethod
    def _notes_with_benefits(cls, notes: str, benefits: object) -> str:
        benefits_text = cls._benefits_text(benefits)
        if not benefits_text:
            return notes.strip()
        marker = f"[BENEFICIOS]\n{benefits_text}\n[/BENEFICIOS]"
        clean_notes = notes.strip()
        if "[BENEFICIOS]" in clean_notes:
            return clean_notes
        return f"{clean_notes}\n\n{marker}".strip()

    @staticmethod
    def _same_job_and_application_url(job_url: str, application_url: str) -> bool:
        return job_url.strip().rstrip("/") == application_url.strip().rstrip("/")

    def _update_existing_application_url(self, reference: SavedLinkedInJob) -> None:
        application_url = reference.application_url.strip()
        if not application_url or self._job_repository is None:
            return
        job = self._job_repository.get_by_url(reference.url)
        if job is None and reference.linkedin_job_id:
            job = self._job_repository.get_by_linkedin_job_id(reference.linkedin_job_id)
        if job is None:
            return
        current = str(getattr(job, "application_url", "") or "").strip()
        if current == application_url:
            return
        job.application_url = application_url
        self._job_repository.update(job)

    def _processed_linkedin_job_ids(self) -> set[str]:
        """Return LinkedIn identifiers already persisted and fully processed."""
        if self._job_repository is None:
            return set()
        getter = getattr(self._job_repository, "get_linkedin_job_ids", None)
        if getter is None:
            return set()
        return set(getter())

    def _delete_closed_job(self, reference: SavedLinkedInJob) -> int:
        if self._job_repository is None:
            return 0
        job = self._job_repository.get_by_url(reference.url)
        if job is None and reference.linkedin_job_id:
            job = self._job_repository.get_by_linkedin_job_id(reference.linkedin_job_id)
        if job is None or job.id is None:
            return 0
        return int(self._job_repository.delete(int(job.id), delete_linked=True))

    def _resolve_company(self, job: ImportedLinkedInJob) -> tuple[int, bool]:
        name = job.company_name.strip() or "Empresa não identificada"
        normalized = self._normalize_name(name)
        for company in self._company_service.list_companies():
            if self._normalize_name(company.name) == normalized:
                return int(company.id), False
        location = job.location.strip()
        city = self._city_from_location(location) or "Não informado"
        company = self._company_service.create_company(
            name=name,
            city=city,
            state=self._state_from_location(location),
            country="Brasil" if location else "",
            linkedin_url="",
            notes="Empresa criada automaticamente durante importação de vagas salvas.",
            data_source="LinkedIn",
            source_reference=job.source_url,
        )
        return int(company.id), True

    @staticmethod
    def _merge_reference(job: ImportedLinkedInJob, reference: SavedLinkedInJob) -> ImportedLinkedInJob:
        return ImportedLinkedInJob(
            title=job.title or reference.title,
            company_name=job.company_name or reference.company_name,
            location=job.location or reference.location,
            work_model=job.work_model or reference.work_model or "Presencial",
            employment_type=job.employment_type or reference.employment_type or "CLT",
            salary_min=job.salary_min or reference.salary_min,
            salary_max=job.salary_max or reference.salary_max,
            currency=job.currency or reference.currency or "BRL",
            recruiter=job.recruiter,
            published_at=job.published_at,
            application_deadline=job.application_deadline,
            description=job.description,
            requirements=job.requirements,
            responsibilities=job.responsibilities,
            benefits=job.benefits,
            source_url=job.source_url or reference.url,
            linkedin_job_id=job.linkedin_job_id or reference.linkedin_job_id,
            confidence=job.confidence,
            source_references=job.source_references,
            accepting_applications=job.accepting_applications,
        )

    def _resolve_recruiter_email(
        self,
        job: ImportedLinkedInJob,
        reference: SavedLinkedInJob,
    ) -> str:
        """Prefer the vacancy e-mail; research only when it is absent."""

        public_email = reference.recruiter_email.strip()
        if public_email:
            return public_email

        service = self._recruiter_email_research_service
        if service is None:
            return ""

        try:
            return service.research(
                RecruiterEmailResearchRequest(
                    company_name=job.company_name or reference.company_name,
                    job_title=job.title or reference.title,
                    location=job.location or reference.location,
                    recruiter_name=job.recruiter,
                )
            )
        except Exception:
            return ""

    @staticmethod
    def _normalize_name(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.casefold())
        return re.sub(r"[^a-z0-9]+", " ", normalized.encode("ascii", "ignore").decode()).strip()

    @staticmethod
    def _city_from_location(value: str) -> str:
        return value.split(",")[0].strip() if value else ""

    @staticmethod
    def _state_from_location(value: str) -> str:
        parts = [part.strip() for part in value.split(",") if part.strip()]
        return parts[1] if len(parts) > 1 else ""

    @staticmethod
    def _emit(callback: Callable[[SavedJobsProgress], None] | None, progress: SavedJobsProgress) -> None:
        if callback is not None:
            callback(progress)

    @staticmethod
    def _raise_if_cancelled(callback: Callable[[], bool] | None) -> None:
        if callback is not None and callback():
            raise LinkedInSavedJobsBrowserError("Importação cancelada pelo usuário.")
