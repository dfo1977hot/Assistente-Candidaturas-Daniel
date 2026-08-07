"""Tests for persisted Resume Optimization preparation."""

from __future__ import annotations

from datetime import UTC, datetime

from acd.application.composition.read_models import (
    ApplicationContext,
    ResumeContext,
)
from acd.application.query_ports import (
    ATSGapQueryDTO,
    ATSHistoryQueryDTO,
    ATSRecommendationQueryDTO,
    VacancyQueryDTO,
)
from acd.application.resume_optimization.resume_optimization_workflow import (
    ResumeOptimizationAvailability,
    ResumeOptimizationWorkflow,
)


class _Applications:
    def __init__(self, context: ApplicationContext | None) -> None:
        self.context = context

    def build(self, application_id: int) -> ApplicationContext | None:
        return self.context if application_id == 1 else None


class _Resumes:
    def __init__(self, ats: ATSHistoryQueryDTO | None, has_resume: bool = True) -> None:
        self.ats = ats
        self.has_resume = has_resume
        self.requested_ids: list[int] = []

    def build(self, curriculum_id: int) -> ResumeContext | None:
        self.requested_ids.append(curriculum_id)
        if not self.has_resume:
            return None
        return ResumeContext(curriculum_id, "v1", "Python")

    def get_persisted_ats_result(self, curriculum_id: int) -> ATSHistoryQueryDTO | None:
        self.requested_ids.append(curriculum_id)
        return self.ats


class _Vacancies:
    def __init__(self, vacancy: VacancyQueryDTO | None) -> None:
        self.vacancy = vacancy
        self.requested_ids: list[int] = []

    def get_by_id(self, job_id: int) -> VacancyQueryDTO | None:
        self.requested_ids.append(job_id)
        return self.vacancy


def _vacancy(
    description: str = "Python and Docker", notes: str = "Remote"
) -> VacancyQueryDTO:
    return VacancyQueryDTO(2, "Backend Engineer", 3, notes, requirements=description)


def _context(curriculum_id: int | None = 4) -> ApplicationContext:
    return ApplicationContext(1, 2, 3, "draft", curriculum_id)


def test_workflow_uses_persisted_ats_without_analysis_services() -> None:
    ats = ATSHistoryQueryDTO(
        1, 4, None, 80.0, datetime(2026, 7, 26, tzinfo=UTC),
        gaps=(ATSGapQueryDTO("Docker", "missing"),),
        recommendations=(ATSRecommendationQueryDTO("Add Docker", "rule"),),
    )
    resumes = _Resumes(ats)

    vacancies = _Vacancies(_vacancy())

    result = ResumeOptimizationWorkflow(_Applications(_context()), resumes, vacancies).execute(1)

    assert result.availability is ResumeOptimizationAvailability.READY
    assert result.curriculum_id == 4
    assert result.gaps == ats.gaps
    assert result.recommendations == ats.recommendations
    assert result.vacancy == _vacancy()
    assert resumes.requested_ids == [4, 4]
    assert vacancies.requested_ids == [2]


def test_workflow_represents_missing_curriculum_and_ats() -> None:
    missing_curriculum = ResumeOptimizationWorkflow(
        _Applications(_context(None)), _Resumes(None), _Vacancies(_vacancy())
    ).execute(1)
    missing_ats = ResumeOptimizationWorkflow(
        _Applications(_context()), _Resumes(None), _Vacancies(_vacancy())
    ).execute(1)

    assert missing_curriculum.availability is ResumeOptimizationAvailability.CURRICULUM_REQUIRED
    assert missing_ats.availability is ResumeOptimizationAvailability.ATS_REQUIRED


def test_workflow_does_not_read_ats_when_associated_curriculum_is_missing() -> None:
    resumes = _Resumes(None, has_resume=False)
    workflow = ResumeOptimizationWorkflow(_Applications(_context()), resumes, _Vacancies(_vacancy()))

    result = workflow.execute(1)

    assert result.availability is ResumeOptimizationAvailability.CURRICULUM_REQUIRED
    assert resumes.requested_ids == [4]


def test_workflow_requires_a_persisted_vacancy_description() -> None:
    ats = ATSHistoryQueryDTO(1, 4, None, 80.0, datetime(2026, 7, 26, tzinfo=UTC))
    vacancies = _Vacancies(_vacancy(description="", notes=""))

    result = ResumeOptimizationWorkflow(_Applications(_context()), _Resumes(ats), vacancies).execute(1)

    assert result.availability is ResumeOptimizationAvailability.VACANCY_REQUIRED
    assert result.vacancy is None
