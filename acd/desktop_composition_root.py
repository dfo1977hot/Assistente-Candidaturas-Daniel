"""The single productive composition root for the desktop application."""

from __future__ import annotations

from acd.core.router import Router
from acd.database.create_database import create_database
from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)
from acd.infrastructure.linkedin.linkedin_saved_jobs_browser import LinkedInSavedJobsBrowser
from acd.infrastructure.repositories.analytics_repository import AnalyticsRepository
from acd.infrastructure.repositories.application_repository import ApplicationRepository
from acd.infrastructure.repositories.ats_repository import ATSRepository
from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.infrastructure.repositories.cover_letter_repository import CoverLetterRepository
from acd.infrastructure.repositories.curriculum_repository import CurriculumRepository
from acd.infrastructure.repositories.interview_repository import InterviewRepository
from acd.infrastructure.repositories.job_profile_repository import JobProfileRepository
from acd.infrastructure.repositories.job_repository import JobRepository
from acd.presentation.pages.agent_console_page import AgentConsolePage
from acd.presentation.pages.application_page import ApplicationPage
from acd.presentation.pages.assistant_page import AssistantPage
from acd.presentation.pages.ats_page import ATSPage
from acd.presentation.pages.candidate_decision_view_model import CandidateDecisionViewModel
from acd.presentation.pages.career_page import CareerPage
from acd.presentation.pages.company_page import CompanyPage
from acd.presentation.pages.curriculum_page import CurriculumPage
from acd.presentation.pages.interview_page import InterviewPage
from acd.presentation.pages.job_page import JobPage
from acd.presentation.pages.letter_page import LetterPage
from acd.presentation.pages.optimized_resume_evaluation_view_model import (
    OptimizedResumeEvaluationViewModel,
)
from acd.presentation.pages.resume_optimization_view_model import ResumeOptimizationViewModel
from acd.presentation.pages.resume_version_review_view_model import ResumeVersionReviewViewModel
from acd.presentation.pages.settings_page import SettingsPage
from acd.presentation.pages.workflow_page import WorkflowPage
from acd.services.analytics_export_service import AnalyticsExportService
from acd.services.analytics_service import AnalyticsService
from acd.services.application_service import ApplicationService
from acd.services.assisted_application_service import AssistedApplicationService
from acd.services.ats_service import ATSService
from acd.services.career_planning_service import CareerPlanningService
from acd.services.closed_linkedin_jobs_registry import ClosedLinkedInJobsRegistry
from acd.services.company_lookup_service import CompanyLookupService
from acd.services.company_service import CompanyService
from acd.services.cover_letter_service import CoverLetterService
from acd.services.curriculum_service import CurriculumService
from acd.services.gap_analysis_service import GapAnalysisService
from acd.services.interview_service import InterviewService
from acd.services.job_service import JobService
from acd.services.linkedin_job_import_service import LinkedInJobImportService
from acd.services.linkedin_saved_jobs_import_service import LinkedInSavedJobsImportService
from acd.services.recruiter_email_research_service import RecruiterEmailResearchService
from acd.services.resume_match_service import ResumeMatchService
from acd.services.salary_research_service import SalaryResearchService
from acd.services.settings_service import SettingsService
from acd.services.workflow_scheduler_service import WorkflowSchedulerService
from acd.services.workflow_service import WorkflowService
from acd.services.workflow_step_registry import ProductiveWorkflowHandlers
from acd.services.workflow_template_service import WorkflowTemplateService
from acd.services.workflow_trigger_dispatcher import WorkflowTriggerDispatcher
from acd.ui.dashboard import Dashboard
from acd.ui.main_window import MainWindow
from acd.ui.sidebar import Sidebar


class DesktopCompositionRoot:
    """Build the runtime object graph without a Kernel, Bootstrap, or DI container.

    The application-wizard is intentionally not composed here; Sprint B owns its
    integration decision.  Legacy Kernel and Bootstrap classes remain available
    for isolated tests and future migration work, but are not runtime entrypoints.
    """

    def build_main_window(self) -> MainWindow:
        """Create persistence, services, pages, router, and the desktop window."""
        create_database()

        company_repository = CompanyRepository()
        job_repository = JobRepository()
        application_repository = ApplicationRepository()
        interview_repository = InterviewRepository()
        curriculum_repository = CurriculumRepository()
        ats_repository = ATSRepository()
        cover_letter_repository = CoverLetterRepository()

        company_service = CompanyService(company_repository)
        job_service = JobService(job_repository)
        closed_jobs_registry = ClosedLinkedInJobsRegistry()
        job_import_service = LinkedInJobImportService(
            closed_jobs_registry=closed_jobs_registry
        )
        settings_service = SettingsService()
        salary_research_service = SalaryResearchService(settings_service=settings_service)
        recruiter_email_research_service = RecruiterEmailResearchService(
            settings_service=settings_service
        )
        saved_jobs_import_service = LinkedInSavedJobsImportService(
            LinkedInSavedJobsBrowser(headless=settings_service.browser_headless),
            job_import_service,
            job_service,
            company_service,
            job_repository,
            salary_research_service,
            recruiter_email_research_service,
            closed_jobs_registry,
        )
        application_service = ApplicationService(application_repository)
        interview_service = InterviewService(interview_repository)
        curriculum_service = CurriculumService(curriculum_repository)
        cover_letter_service = CoverLetterService(
            cover_letter_repository,
            job_service,
            curriculum_service,
            settings_service,
        )
        analytics_service = AnalyticsService(AnalyticsRepository())
        analytics_export_service = AnalyticsExportService()
        career_service = CareerPlanningService()
        gap_service = GapAnalysisService()
        ats_service = ATSService(ats_repository)
        resume_match_service = ResumeMatchService()
        workflow_handlers = ProductiveWorkflowHandlers(
            job_service=job_service,
            application_service=application_service,
            company_service=company_service,
            company_lookup_service=CompanyLookupService(
                settings_service=settings_service,
            ),
            salary_research_service=salary_research_service,
            resume_match_service=resume_match_service,
            curriculum_service=curriculum_service,
            cover_letter_service=cover_letter_service,
            application_url_resolver=PlaywrightApplicationBrowser(
                linkedin_headless=settings_service.browser_headless,
            ),
        )
        workflow_service = WorkflowService(step_registry=workflow_handlers.registry())
        workflow_trigger_dispatcher = WorkflowTriggerDispatcher(
            workflow_service, workflow_service.event_bus
        )
        workflow_scheduler_service = WorkflowSchedulerService(workflow_service)
        job_service.set_event_dispatcher(workflow_trigger_dispatcher.dispatch)
        application_service.set_event_dispatcher(workflow_trigger_dispatcher.dispatch)
        workflow_template_service = WorkflowTemplateService(workflow_service)
        assisted_application_service = AssistedApplicationService(
            PlaywrightApplicationBrowser(
                linkedin_headless=settings_service.browser_headless,
            )
        )

        application_view_models = self._build_application_view_models(
            application_repository, curriculum_repository, company_repository,
            job_repository, ats_repository, interview_repository,
        )
        router = Router()
        curriculum_page = CurriculumPage(curriculum_service)

        def open_optimized_curriculum(curriculum_id: int) -> None:
            router.navigate("curricula")
            curriculum_page.open_curriculum(curriculum_id)

        application_page = ApplicationPage(
            candidate_decision_view_model=application_view_models["candidate_decision"],
            on_candidate_decision_action=lambda action: self._navigate(router, action),
            on_optimized_curriculum_created=open_optimized_curriculum,
            resume_optimization_view_model=application_view_models["resume_optimization"],
            resume_version_review_view_model=application_view_models["resume_review"],
            optimized_resume_evaluation_view_model=application_view_models["optimized_evaluation"],
            application_service=application_service,
            company_service=company_service,
            job_service=job_service,
            curriculum_service=curriculum_service,
            resume_match_service=resume_match_service,
            ats_service=ats_service,
            assisted_application_service=assisted_application_service,
        )

        def navigate_to_analytics_record(entity_type: str, _entity_id: int) -> None:
            destinations = {
                "application": "applications",
                "job": "jobs",
                "workflow": "workflows",
                "cover_letter": "cover_letters",
            }
            if destination := destinations.get(entity_type):
                router.navigate(destination)

        dashboard = Dashboard(
            analytics_service,
            workflow_service.event_bus,
            analytics_export_service,
            navigate_to_analytics_record,
        )
        analytics_dashboard = Dashboard(
            analytics_service,
            workflow_service.event_bus,
            analytics_export_service,
            navigate_to_analytics_record,
        )
        pages = {
            "dashboard": dashboard,
            "companies": CompanyPage(
                company_service,
                lambda provider_name: CompanyLookupService(
                    provider_name=provider_name,
                    settings_service=settings_service,
                ),
            ),
            "jobs": JobPage(
                job_service,
                company_service,
                job_import_service,
                saved_jobs_import_service,
                salary_research_service,
                recruiter_email_research_service,
                PlaywrightApplicationBrowser(
                    linkedin_headless=settings_service.browser_headless,
                ),
            ),
            "applications": application_page,
            "interviews": InterviewPage(interview_service, application_service),
            "curricula": curriculum_page,
            "workflows": WorkflowPage(
                workflow_template_service,
                workflow_service,
                job_service,
                application_service,
                curriculum_service,
                workflow_scheduler_service,
            ),
            "analytics": analytics_dashboard,
            "career": CareerPage(career_service, gap_service),
            "assistant": self._build_assistant_page(),
            "agent_console": self._build_agent_console_page(),
            "cover_letters": LetterPage(
                cover_letter_service,
                job_service,
                curriculum_service,
            ),
            "crm": ATSPage(ats_service),
            "settings": SettingsPage(settings_service),
        }
        return MainWindow(sidebar=Sidebar(), router=router, pages=pages, settings_service=settings_service)

    @staticmethod
    def _build_application_view_models(
        application_repository: ApplicationRepository,
        curriculum_repository: CurriculumRepository,
        company_repository: CompanyRepository,
        job_repository: JobRepository,
        ats_repository: ATSRepository,
        interview_repository: InterviewRepository,
    ) -> dict[str, object]:
        """Wire the established resume/candidate flow directly, without a container."""
        from acd.application.candidate_decision_service import CandidateDecisionService
        from acd.application.candidate_decision_use_case import CandidateDecisionUseCase
        from acd.application.composition.application_context_service import (
            ApplicationContextService,
        )
        from acd.application.composition.ats_context_adapter import ATSContextAdapter
        from acd.application.composition.interview_context_service import InterviewContextService
        from acd.application.composition.resume_context_service import ResumeContextService
        from acd.application.optimized_resume_evaluation_use_case import (
            OptimizedResumeEvaluationUseCase,
        )
        from acd.application.resume_optimization.resume_optimization_use_case import (
            ResumeOptimizationUseCase,
        )
        from acd.application.resume_optimization.resume_optimization_workflow import (
            ResumeOptimizationWorkflow,
        )
        from acd.application.resume_version_review_use_case import ResumeVersionReviewUseCase
        from acd.domain.ats_evaluation import ATSEvaluator
        from acd.infrastructure.query_adapters.application_query_adapter import (
            ApplicationQueryAdapter,
        )
        from acd.infrastructure.query_adapters.ats_history_query_adapter import (
            ATSHistoryQueryAdapter,
        )
        from acd.infrastructure.query_adapters.company_query_adapter import CompanyQueryAdapter
        from acd.infrastructure.query_adapters.generated_resume_version_query_adapter import (
            GeneratedResumeVersionQueryAdapter,
        )
        from acd.infrastructure.query_adapters.interview_query_adapter import InterviewQueryAdapter
        from acd.infrastructure.query_adapters.resume_query_adapter import ResumeQueryAdapter
        from acd.infrastructure.query_adapters.vacancy_query_adapter import VacancyQueryAdapter
        from acd.services.ai_generation_service import ResumeGenerationService
        from acd.services.ats_service import (
            GapAnalysisEngine,
            RuleBasedRecommendationStrategy,
            RuleBasedScoreEngine,
        )

        application_query = ApplicationQueryAdapter(application_repository)
        resume_context = ResumeContextService(
            ResumeQueryAdapter(curriculum_repository), ATSHistoryQueryAdapter(ats_repository), ATSContextAdapter()
        )
        application_context = ApplicationContextService(application_query)
        vacancy_query = VacancyQueryAdapter(job_repository, JobProfileRepository())
        interview_context = InterviewContextService(
            application_query, application_context, resume_context,
            CompanyQueryAdapter(company_repository), vacancy_query, InterviewQueryAdapter(interview_repository),
        )
        workflow = ResumeOptimizationWorkflow(application_context, resume_context, vacancy_query)
        version_query = GeneratedResumeVersionQueryAdapter()
        return {
            "candidate_decision": CandidateDecisionViewModel(CandidateDecisionUseCase(CandidateDecisionService(interview_context))),
            "resume_optimization": ResumeOptimizationViewModel(ResumeOptimizationUseCase(workflow, ResumeGenerationService())),
            "resume_review": ResumeVersionReviewViewModel(ResumeVersionReviewUseCase(application_context, resume_context, version_query)),
            "optimized_evaluation": OptimizedResumeEvaluationViewModel(
                OptimizedResumeEvaluationUseCase(
                    application_context, resume_context, version_query, vacancy_query,
                    ATSEvaluator(RuleBasedScoreEngine(), GapAnalysisEngine(), RuleBasedRecommendationStrategy()),
                )
            ),
        }

    @staticmethod
    def _navigate(router: Router, action_id: str) -> None:
        destinations = {
            "review_gaps": "career",
            "prepare_curriculum": "curricula",
            "prepare_interview": "interviews",
        }
        if destination := destinations.get(action_id):
            router.navigate(destination)

    @staticmethod
    def _build_assistant_page() -> AssistantPage:
        from acd.infrastructure.agent.ai_orchestrator import AIOrchestrator
        from acd.infrastructure.agent.tool_registry import DefaultToolRegistry
        from acd.infrastructure.repositories.agent.agent_repository import AgentRepository
        from acd.services.ai_execution_service import AgentMemoryService, AIExecutionService

        repository = AgentRepository()
        return AssistantPage(
            orchestrator=AIOrchestrator(tool_registry=DefaultToolRegistry()),
            repository=repository,
            memory_service=AgentMemoryService(repository),
            execution_service=AIExecutionService(repository),
        )

    @staticmethod
    def _build_agent_console_page() -> AgentConsolePage:
        from acd.infrastructure.agents.capability_service import CapabilityService
        from acd.infrastructure.agents.context import ContextManager
        from acd.infrastructure.agents.message_bus import MessageBus
        from acd.infrastructure.agents.registry import AgentRegistry
        from acd.infrastructure.agents.task_scheduler import TaskScheduler
        from acd.infrastructure.repositories.agents.agent_repository import AgentRepository
        from acd.services.agents.supervisor_service import SupervisorService

        registry = AgentRegistry()
        message_bus = MessageBus()
        context_manager = ContextManager()
        task_scheduler = TaskScheduler()
        capability_service = CapabilityService()
        repository = AgentRepository()
        return AgentConsolePage(
            registry=registry,
            message_bus=message_bus,
            context_manager=context_manager,
            task_scheduler=task_scheduler,
            capability_service=capability_service,
            repository=repository,
            supervisor=SupervisorService(
                registry=registry,
                message_bus=message_bus,
                context_manager=context_manager,
                task_scheduler=task_scheduler,
                capability_service=capability_service,
                repository=repository,
            ),
        )
