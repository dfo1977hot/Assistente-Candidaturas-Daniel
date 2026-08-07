"""Composition-root registration for Application query adapters."""

from __future__ import annotations

from acd.application.application_resume_selection_port import ApplicationResumeSelectionPort
from acd.application.candidate_decision_service import CandidateDecisionService
from acd.application.candidate_decision_use_case import CandidateDecisionUseCase
from acd.application.composition.application_context_service import ApplicationContextService
from acd.application.composition.ats_context_adapter import ATSContextAdapter
from acd.application.composition.interview_context_service import InterviewContextService
from acd.application.composition.resume_context_service import ResumeContextService
from acd.application.effective_application_resume_use_case import EffectiveApplicationResumeUseCase
from acd.application.effective_structured_resume_docx_export import (
    ExportEffectiveStructuredResumeDocxUseCase,
    StructuredResumeDocxExportPort,
)
from acd.application.optimized_resume_evaluation_use_case import (
    OptimizedResumeEvaluationUseCase,
)
from acd.application.query_ports import (
    ApplicationQueryPort,
    ATSHistoryQueryPort,
    CompanyQueryPort,
    GeneratedResumeVersionQueryPort,
    InterviewQueryPort,
    ResumeQueryPort,
    VacancyQueryPort,
)
from acd.application.resume_adoption_use_cases import (
    AdoptResumeVersionUseCase,
    UseOriginalResumeUseCase,
)
from acd.application.resume_optimization.resume_optimization_use_case import (
    ResumeOptimizationUseCase,
)
from acd.application.resume_optimization.resume_optimization_workflow import (
    ResumeOptimizationWorkflow,
)
from acd.application.resume_version_review_use_case import ResumeVersionReviewUseCase
from acd.application.structured_resume_generation import StructuredResumeGenerationPort
from acd.application.structured_resume_version_generation import (
    GenerateStructuredResumeVersionUseCase,
    StructuredResumeTextRenderer,
    StructuredResumeVersionWritePort,
)
from acd.core.kernel.dependency_container import DependencyContainer
from acd.domain.ats_evaluation import ATSEvaluator
from acd.infrastructure.ai.openai_structured_resume_provider import (
    create_structured_resume_generation_provider,
)
from acd.infrastructure.query_adapters.application_query_adapter import ApplicationQueryAdapter
from acd.infrastructure.query_adapters.application_resume_selection_adapter import (
    ApplicationResumeSelectionAdapter,
)
from acd.infrastructure.query_adapters.ats_history_query_adapter import ATSHistoryQueryAdapter
from acd.infrastructure.query_adapters.company_query_adapter import CompanyQueryAdapter
from acd.infrastructure.query_adapters.generated_resume_version_query_adapter import (
    GeneratedResumeVersionQueryAdapter,
)
from acd.infrastructure.query_adapters.interview_query_adapter import InterviewQueryAdapter
from acd.infrastructure.query_adapters.resume_query_adapter import ResumeQueryAdapter
from acd.infrastructure.query_adapters.vacancy_query_adapter import VacancyQueryAdapter
from acd.infrastructure.repositories.application_repository import ApplicationRepository
from acd.infrastructure.repositories.ats_repository import ATSRepository
from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.infrastructure.repositories.curriculum_repository import CurriculumRepository
from acd.infrastructure.repositories.interview_repository import InterviewRepository
from acd.infrastructure.repositories.job_profile_repository import JobProfileRepository
from acd.infrastructure.repositories.job_repository import JobRepository
from acd.infrastructure.repositories.structured_resume_version_write_adapter import (
    StructuredResumeVersionWriteAdapter,
)
from acd.infrastructure.structured_resume_docx_export_adapter import (
    PythonDocxStructuredResumeExportAdapter,
)
from acd.services.ai_generation_service import ResumeGenerationService
from acd.services.ats_service import (
    GapAnalysisEngine,
    RuleBasedRecommendationStrategy,
    RuleBasedScoreEngine,
)


def register_application_composition(
    container: DependencyContainer,
    *,
    application_repository: ApplicationRepository,
    curriculum_repository: CurriculumRepository,
    company_repository: CompanyRepository,
    job_repository: JobRepository,
    job_profile_repository: JobProfileRepository,
    ats_repository: ATSRepository,
    interview_repository: InterviewRepository,
) -> None:
    """Register query adapters and composition services by their contracts."""
    container.register_factory(
        ApplicationQueryPort,
        lambda: ApplicationQueryAdapter(application_repository),
    )
    container.register_factory(
        ApplicationResumeSelectionPort,
        lambda: ApplicationResumeSelectionAdapter(application_repository),
    )
    container.register_factory(
        ResumeQueryPort,
        lambda: ResumeQueryAdapter(curriculum_repository),
    )
    container.register_factory(
        GeneratedResumeVersionQueryPort,
        GeneratedResumeVersionQueryAdapter,
    )
    container.register_factory(
        StructuredResumeGenerationPort,
        create_structured_resume_generation_provider,
    )
    container.register_factory(
        StructuredResumeVersionWritePort,
        StructuredResumeVersionWriteAdapter,
    )
    container.register_factory(
        StructuredResumeDocxExportPort,
        PythonDocxStructuredResumeExportAdapter,
    )
    container.register_factory(
        CompanyQueryPort,
        lambda: CompanyQueryAdapter(company_repository),
    )
    container.register_factory(
        VacancyQueryPort,
        lambda: VacancyQueryAdapter(job_repository, job_profile_repository),
    )
    container.register_factory(
        ATSHistoryQueryPort,
        lambda: ATSHistoryQueryAdapter(ats_repository),
    )
    container.register_factory(
        InterviewQueryPort,
        lambda: InterviewQueryAdapter(interview_repository),
    )
    container.register_singleton(ATSContextAdapter, ATSContextAdapter())
    container.register_factory(
        ApplicationContextService,
        lambda: ApplicationContextService(container.resolve(ApplicationQueryPort)),
    )
    container.register_factory(
        ResumeContextService,
        lambda: ResumeContextService(
            container.resolve(ResumeQueryPort),
            container.resolve(ATSHistoryQueryPort),
            container.resolve(ATSContextAdapter),
        ),
    )
    container.register_factory(
        InterviewContextService,
        lambda: InterviewContextService(
            container.resolve(ApplicationQueryPort),
            container.resolve(ApplicationContextService),
            container.resolve(ResumeContextService),
            container.resolve(CompanyQueryPort),
            container.resolve(VacancyQueryPort),
            container.resolve(InterviewQueryPort),
        ),
    )
    container.register_factory(
        CandidateDecisionService,
        lambda: CandidateDecisionService(container.resolve(InterviewContextService)),
    )
    container.register_factory(
        CandidateDecisionUseCase,
        lambda: CandidateDecisionUseCase(container.resolve(CandidateDecisionService)),
    )
    container.register_factory(
        ResumeOptimizationWorkflow,
        lambda: ResumeOptimizationWorkflow(
            container.resolve(ApplicationContextService),
            container.resolve(ResumeContextService),
            container.resolve(VacancyQueryPort),
        ),
    )
    container.register_factory(
        ResumeOptimizationUseCase,
        lambda: ResumeOptimizationUseCase(
            container.resolve(ResumeOptimizationWorkflow), ResumeGenerationService()
        ),
    )
    container.register_factory(
        GenerateStructuredResumeVersionUseCase,
        lambda: GenerateStructuredResumeVersionUseCase(
            container.resolve(ResumeOptimizationWorkflow),
            container.resolve(StructuredResumeGenerationPort),
            StructuredResumeTextRenderer(),
            container.resolve(StructuredResumeVersionWritePort),
        ),
    )
    container.register_factory(
        ResumeVersionReviewUseCase,
        lambda: ResumeVersionReviewUseCase(
            container.resolve(ApplicationContextService),
            container.resolve(ResumeContextService),
            container.resolve(GeneratedResumeVersionQueryPort),
        ),
    )
    container.register_factory(
        EffectiveApplicationResumeUseCase,
        lambda: EffectiveApplicationResumeUseCase(
            container.resolve(ApplicationContextService),
            container.resolve(ResumeQueryPort),
            container.resolve(GeneratedResumeVersionQueryPort),
        ),
    )
    container.register_factory(
        ExportEffectiveStructuredResumeDocxUseCase,
        lambda: ExportEffectiveStructuredResumeDocxUseCase(
            container.resolve(EffectiveApplicationResumeUseCase),
            container.resolve(StructuredResumeDocxExportPort),
        ),
    )
    container.register_factory(
        AdoptResumeVersionUseCase,
        lambda: AdoptResumeVersionUseCase(
            container.resolve(ApplicationContextService),
            container.resolve(GeneratedResumeVersionQueryPort),
            container.resolve(ApplicationResumeSelectionPort),
        ),
    )
    container.register_factory(
        UseOriginalResumeUseCase,
        lambda: UseOriginalResumeUseCase(
            container.resolve(ApplicationContextService),
            container.resolve(ApplicationResumeSelectionPort),
        ),
    )
    container.register_factory(
        ATSEvaluator,
        lambda: ATSEvaluator(
            RuleBasedScoreEngine(),
            GapAnalysisEngine(),
            RuleBasedRecommendationStrategy(),
        ),
    )
    container.register_factory(
        OptimizedResumeEvaluationUseCase,
        lambda: OptimizedResumeEvaluationUseCase(
            container.resolve(ApplicationContextService),
            container.resolve(ResumeContextService),
            container.resolve(GeneratedResumeVersionQueryPort),
            container.resolve(VacancyQueryPort),
            container.resolve(ATSEvaluator),
        ),
    )
