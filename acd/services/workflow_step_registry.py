from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict
from types import SimpleNamespace
from typing import Any

from acd.services.application_service import ApplicationService
from acd.services.company_lookup_service import CompanyLookupService
from acd.services.company_service import CompanyService
from acd.services.cover_letter_service import CoverLetterService
from acd.services.curriculum_service import CurriculumService
from acd.services.job_service import JobService
from acd.services.linkedin_application_resolver import LinkedInApplicationResolver
from acd.services.resume_match_service import ResumeMatchService
from acd.services.salary_research_service import (
    SalaryResearchRequest,
    SalaryResearchService,
)

WorkflowContext = dict[str, Any]
WorkflowStep = dict[str, Any]
WorkflowStepResult = dict[str, Any]
WorkflowStepHandler = Callable[[WorkflowStep, WorkflowContext], WorkflowStepResult]


class WorkflowStepRegistry:
    """Resolve workflow commands without embedding business rules in the runner."""

    JOB_COMMANDS = frozenset(
        {
            "verify_job",
            "detect_application_url",
            "enrich_company",
            "research_salary",
            "analyze_fit",
            "select_resume",
            "generate_resume",
            "generate_cover_letter",
            "register_application",
            "review_application",
            "classify_closed_job",
        }
    )

    def __init__(
        self,
        handlers: Mapping[str, WorkflowStepHandler] | None = None,
    ) -> None:
        self._handlers = dict(handlers or {})

    def register(self, command: str, handler: WorkflowStepHandler) -> None:
        self._handlers[command] = handler

    def resolve(self, command: str) -> WorkflowStepHandler | None:
        return self._handlers.get(command)

    def commands(self) -> tuple[str, ...]:
        return tuple(self._handlers)

    def requires_job(self, command: str) -> bool:
        return command in self.JOB_COMMANDS


class ProductiveWorkflowHandlers:
    """Adapters that orchestrate the existing productive application services."""

    def __init__(
        self,
        *,
        job_service: JobService,
        application_service: ApplicationService,
        company_service: CompanyService,
        company_lookup_service: CompanyLookupService,
        salary_research_service: SalaryResearchService,
        resume_match_service: ResumeMatchService,
        curriculum_service: CurriculumService,
        cover_letter_service: CoverLetterService,
        application_url_resolver: LinkedInApplicationResolver,
    ) -> None:
        self.job_service = job_service
        self.application_service = application_service
        self.company_service = company_service
        self.company_lookup_service = company_lookup_service
        self.salary_research_service = salary_research_service
        self.resume_match_service = resume_match_service
        self.curriculum_service = curriculum_service
        self.cover_letter_service = cover_letter_service
        self.application_url_resolver = application_url_resolver

    def registry(self) -> WorkflowStepRegistry:
        return WorkflowStepRegistry(
            {
                "verify_job": self.verify_job,
                "detect_application_url": self.detect_application_url,
                "enrich_company": self.enrich_company,
                "research_salary": self.research_salary,
                "analyze_fit": self.analyze_fit,
                "select_resume": self.select_resume,
                "generate_resume": self.generate_resume,
                "generate_cover_letter": self.generate_cover_letter,
                "register_application": self.register_application,
            }
        )

    def verify_job(self, _step: WorkflowStep, context: WorkflowContext) -> WorkflowStepResult:
        job = self._job(context)
        return self._completed(
            f'Vaga "{job.title}" localizada.',
            job_id=job.id,
            company_id=job.company_id,
        )

    def detect_application_url(
        self, _step: WorkflowStep, context: WorkflowContext
    ) -> WorkflowStepResult:
        job = self._job(context)
        if not job.job_url:
            return self._ignored("A vaga não possui URL de origem para inspeção.")
        if "linkedin.com" not in job.job_url.casefold():
            return self._ignored("Detecção automática disponível somente para LinkedIn.")
        resolution = self.application_url_resolver.resolve_linkedin_application_url(
            job.job_url
        )
        if resolution.url:
            self._update_job(job, application_url=resolution.url)
            return self._completed(
                "URL de candidatura localizada e salva.",
                application_url=resolution.url,
                application_type=resolution.application_type,
            )
        if resolution.accepting_applications is False:
            return self._ignored("A plataforma informa que a vaga não aceita candidaturas.")
        return self._ignored(
            "A URL não pôde ser resolvida; a vaga não foi classificada como encerrada."
        )

    def enrich_company(
        self, _step: WorkflowStep, context: WorkflowContext
    ) -> WorkflowStepResult:
        job = self._job(context)
        company = getattr(job, "company", None)
        if company is None:
            raise ValueError("A empresa vinculada à vaga não foi localizada.")
        results = self.company_lookup_service.search(company.name)
        if not results:
            return self._ignored("Nenhum dado público confiável foi encontrado.")
        found = results[0]
        updated = self.company_service.update_company(
            company.id,
            name=found.name or company.name,
            city=found.city or company.city,
            segment=found.segment or company.segment,
            state=found.state or company.state,
            country=found.country or company.country,
            company_size=company.company_size,
            website=found.website or company.website,
            linkedin_url=company.linkedin_url,
            notes=company.notes,
            legal_name=found.legal_name or company.legal_name,
            tax_id=found.tax_id or company.tax_id,
            registration_status=(
                found.registration_status or company.registration_status
            ),
            address=found.address or company.address,
            postal_code=found.postal_code or company.postal_code,
            phone=found.phone or company.phone,
            data_source=found.source or company.data_source,
            source_reference=found.source_reference or company.source_reference,
            data_retrieved_at=found.retrieved_at or company.data_retrieved_at,
        )
        if updated is None:
            raise ValueError("A empresa vinculada à vaga não foi localizada.")
        return self._completed("Dados da empresa atualizados.", company_id=updated.id)

    def research_salary(
        self, _step: WorkflowStep, context: WorkflowContext
    ) -> WorkflowStepResult:
        job = self._job(context)
        result = self.salary_research_service.research(
            SalaryResearchRequest(
                title=job.title,
                location=job.location,
                work_model=job.work_model,
                employment_type=job.employment_type,
            )
        )
        self._update_job(job, salary_max=result.salary_max, currency=result.currency)
        return self._completed(
            "Remuneração ideal atualizada sem alterar a remuneração oferecida.",
            salary_ideal=result.salary_max,
            currency=result.currency,
        )

    def analyze_fit(
        self, _step: WorkflowStep, context: WorkflowContext
    ) -> WorkflowStepResult:
        job = self._job(context)
        curriculum = self._curriculum(context)
        application = self._application_for_job(job.id, context.get("application_id"))
        target = application or SimpleNamespace(id=0, job_id=job.id, job=job)
        result = self.resume_match_service.analyze(
            application=target,
            curriculum=curriculum,
        )
        return self._completed(
            f"Aderência analisada: {result.score:.1f}%.",
            curriculum_id=curriculum.id,
            fit_score=result.score,
            fit_metadata=asdict(result),
        )

    def select_resume(
        self, _step: WorkflowStep, context: WorkflowContext
    ) -> WorkflowStepResult:
        job = self._job(context)
        curricula = self.curriculum_service.list_curricula()
        if not curricula:
            raise ValueError("Nenhum currículo está disponível para seleção.")
        application = self._application_for_job(job.id, context.get("application_id"))
        target = application or SimpleNamespace(id=0, job_id=job.id, job=job)
        scored = [
            (
                self.resume_match_service.analyze(
                    application=target,
                    curriculum=curriculum,
                ).score,
                curriculum,
            )
            for curriculum in curricula
        ]
        score, selected = max(scored, key=lambda item: item[0])
        return self._completed(
            f'Currículo "{selected.name}" selecionado ({score:.1f}%).',
            curriculum_id=selected.id,
            fit_score=score,
        )

    def generate_resume(
        self, _step: WorkflowStep, context: WorkflowContext
    ) -> WorkflowStepResult:
        source = self._curriculum(context)
        generated = self.curriculum_service.create_optimized_curriculum(
            source_curriculum_id=source.id
        )
        if generated is None:
            raise ValueError("Não foi possível gerar a nova versão do currículo.")
        return self._completed(
            f"Currículo versionado como {generated.version}.",
            curriculum_id=generated.id,
            curriculum_version=generated.version,
        )

    def generate_cover_letter(
        self, _step: WorkflowStep, context: WorkflowContext
    ) -> WorkflowStepResult:
        job = self._job(context)
        curriculum = self._curriculum(context)
        letter = self.cover_letter_service.generate_letter(
            job_id=job.id,
            curriculum_id=curriculum.id,
            letter_type="Carta de Apresentação",
            language="Português",
            tone="Profissional",
            length="Média",
        )
        return self._completed(
            f"Nova versão da carta gerada: {letter.version}.",
            cover_letter_id=letter.id,
            cover_letter_version=letter.version,
        )

    def register_application(
        self, _step: WorkflowStep, context: WorkflowContext
    ) -> WorkflowStepResult:
        job = self._job(context)
        application = self._application_for_job(job.id, context.get("application_id"))
        if application is None:
            application = self.application_service.create_application(
                job_id=job.id,
                company_id=job.company_id,
                salary_expected=job.salary_max,
                salary_offered=job.salary_min,
                response_date=None,
                application_channel=job.source or "",
                recruiter_name=job.recruiter or "",
                recruiter_email=job.recruiter_email or "",
            )
            message = "Candidatura criada sem duplicidade."
        else:
            application = self.application_service.update_application(
                application.id,
                job_id=job.id,
                company_id=job.company_id,
                status=application.status,
                application_date=self._iso(application.application_date),
                next_follow_up=self._iso(application.next_follow_up),
                response_date=self._iso(application.response_date),
                salary_expected=job.salary_max,
                salary_offered=job.salary_min,
                application_channel=application.application_channel or "",
                recruiter_name=application.recruiter_name or job.recruiter or "",
                recruiter_email=application.recruiter_email or job.recruiter_email or "",
                recruiter_phone=application.recruiter_phone or "",
                feedback=application.feedback or "",
                notes=application.notes or "",
            )
            if application is None:
                raise ValueError("A candidatura relacionada não foi localizada.")
            message = "Candidatura existente atualizada."
        curriculum_id = context.get("curriculum_id")
        if curriculum_id:
            self.curriculum_service.associate_to_application(
                application_id=application.id,
                curriculum_id=int(curriculum_id),
            )
        return self._completed(message, application_id=application.id)

    def _job(self, context: WorkflowContext) -> Any:
        job_id = context.get("job_id")
        if not job_id:
            raise ValueError("Selecione uma vaga antes de executar esta etapa.")
        job = self.job_service.get_job(int(job_id))
        if job is None:
            raise ValueError("A vaga selecionada não foi localizada.")
        return job

    def _curriculum(self, context: WorkflowContext) -> Any:
        curriculum_id = context.get("curriculum_id")
        if not curriculum_id:
            raise ValueError("Selecione um currículo antes de executar esta etapa.")
        curriculum = next(
            (
                item
                for item in self.curriculum_service.list_curricula()
                if item.id == int(curriculum_id)
            ),
            None,
        )
        if curriculum is None:
            raise ValueError("O currículo selecionado não foi localizado.")
        return curriculum

    def _application_for_job(self, job_id: int, application_id: Any = None) -> Any:
        if application_id:
            application = self.application_service.get_application(int(application_id))
            if application is not None and application.job_id == job_id:
                return application
        return next(
            (
                item
                for item in self.application_service.list_applications()
                if item.job_id == job_id
            ),
            None,
        )

    def _update_job(self, job: Any, **changes: Any) -> Any:
        values = {
            "company_id": job.company_id,
            "title": job.title,
            "location": job.location or "",
            "work_model": job.work_model or "",
            "employment_type": job.employment_type or "",
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "currency": job.currency or "",
            "status": job.status or "Nova",
            "source": job.source or "",
            "job_url": job.job_url or "",
            "application_url": job.application_url or "",
            "recruiter": job.recruiter or "",
            "recruiter_email": job.recruiter_email or "",
            "application_deadline": self._iso(job.application_deadline),
            "application_date": self._iso(job.application_date),
            "priority": job.priority,
            "notes": job.notes or "",
        }
        values.update(changes)
        updated = self.job_service.update_job(job.id, **values)
        if updated is None:
            raise ValueError("A vaga selecionada não foi localizada.")
        return updated

    @staticmethod
    def _iso(value: Any) -> str | None:
        return value.isoformat() if value is not None else None

    @staticmethod
    def _completed(message: str, **updates: Any) -> WorkflowStepResult:
        return {"status": "Concluída", "message": message, "context_updates": updates}

    @staticmethod
    def _ignored(message: str) -> WorkflowStepResult:
        return {"status": "Ignorada", "message": message, "context_updates": {}}
