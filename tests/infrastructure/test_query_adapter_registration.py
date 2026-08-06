"""Tests for Application query adapter dependency registration."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from acd.application.candidate_decision_service import CandidateDecisionService
from acd.application.candidate_decision_use_case import CandidateDecisionUseCase
from acd.application.composition.application_context_service import ApplicationContextService
from acd.application.composition.interview_context_service import InterviewContextService
from acd.application.composition.resume_context_service import ResumeContextService
from acd.application.query_ports import (
    ApplicationQueryPort,
    ATSHistoryQueryPort,
    CompanyQueryPort,
    GeneratedResumeVersionQueryPort,
    InterviewQueryPort,
    ResumeQueryPort,
    VacancyQueryPort,
)
from acd.application.resume_optimization.resume_optimization_use_case import (
    ResumeOptimizationUseCase,
)
from acd.application.resume_optimization.resume_optimization_workflow import (
    ResumeOptimizationWorkflow,
)
from acd.application.resume_version_review_use_case import ResumeVersionReviewUseCase
from acd.application.structured_resume_generation import StructuredResumeGenerationPort
from acd.core.kernel.dependency_container import DependencyContainer
from acd.infrastructure.query_adapters.registration import register_application_composition


class FakeApplicationRepository:
    """Application repository double."""

    def get_by_id(self, application_id: int) -> object | None:
        if application_id != 1:
            return None
        return SimpleNamespace(
            id=1,
            job_id=2,
            company_id=3,
            curriculum_id=4,
            curriculum_version="v1",
            status="Interview",
        )

    def get_followups(self, application_id: int) -> list[object]:
        return []


class FakeCurriculumRepository:
    """Curriculum repository double."""

    def get_by_id(self, curriculum_id: int) -> object | None:
        if curriculum_id != 4:
            return None
        return SimpleNamespace(id=4, name="Daniel", version="v1", language="pt-BR", description="Python")

    def get_versions(self, curriculum_id: int) -> list[object]:
        return []


class FakeCompanyRepository:
    """Company repository double."""

    def get_by_id(self, company_id: int) -> object | None:
        return SimpleNamespace(id=3, name="ACD", segment="Technology") if company_id == 3 else None


class FakeJobRepository:
    """Job repository double."""

    def get_by_id(self, job_id: int) -> object | None:
        return SimpleNamespace(id=2, title="Backend Engineer", company_id=3, notes="Remote") if job_id == 2 else None


class FakeJobProfileRepository:
    """Job profile repository double."""

    def get_by_job(self, job_id: int) -> object | None:
        return SimpleNamespace(skills="Python", raw_description="Python") if job_id == 2 else None


class FakeATSRepository:
    """ATS repository double."""

    def get_history(self) -> list[object]:
        return [SimpleNamespace(id=10, curriculum_id=4, job_profile_id=None, total_score=82, calculated_at=datetime.now(UTC))]


class FakeInterviewRepository:
    """Interview repository double."""

    def get_all(self) -> list[object]:
        return []


def test_registration_resolves_all_query_ports_and_composition_services() -> None:
    """The container resolves every contract without concrete adapter requests."""
    container = DependencyContainer()

    register_application_composition(
        container,
        application_repository=FakeApplicationRepository(),
        curriculum_repository=FakeCurriculumRepository(),
        company_repository=FakeCompanyRepository(),
        job_repository=FakeJobRepository(),
        job_profile_repository=FakeJobProfileRepository(),
        ats_repository=FakeATSRepository(),
        interview_repository=FakeInterviewRepository(),
    )

    for port in (
        ApplicationQueryPort,
        ResumeQueryPort,
        GeneratedResumeVersionQueryPort,
        CompanyQueryPort,
        VacancyQueryPort,
        ATSHistoryQueryPort,
        InterviewQueryPort,
        StructuredResumeGenerationPort,
    ):
        assert container.contains(port)
        assert container.resolve(port) is not None
    assert isinstance(container.resolve(ApplicationContextService), ApplicationContextService)
    assert isinstance(container.resolve(ResumeContextService), ResumeContextService)
    assert isinstance(container.resolve(InterviewContextService), InterviewContextService)
    assert isinstance(container.resolve(CandidateDecisionService), CandidateDecisionService)
    assert isinstance(container.resolve(CandidateDecisionUseCase), CandidateDecisionUseCase)
    assert isinstance(container.resolve(ResumeOptimizationWorkflow), ResumeOptimizationWorkflow)
    assert isinstance(container.resolve(ResumeOptimizationUseCase), ResumeOptimizationUseCase)
    assert isinstance(container.resolve(ResumeVersionReviewUseCase), ResumeVersionReviewUseCase)
    assert not container.resolve(StructuredResumeGenerationPort).get_capabilities().supports_structured_resume
