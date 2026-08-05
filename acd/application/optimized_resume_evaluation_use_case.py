"""Transient ATS evaluation for one generated resume version."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from acd.application.composition.application_context_service import ApplicationContextService
from acd.application.composition.resume_context_service import ResumeContextService
from acd.application.query_ports import GeneratedResumeVersionQueryPort, VacancyQueryPort
from acd.domain.ats_evaluation import ATSEvaluationInput, ATSEvaluator


class OptimizedResumeEvaluationStatus(StrEnum):
    """Functional outcomes for an optimized resume evaluation."""

    APPLICATION_NOT_FOUND = "application_not_found"
    CURRICULUM_REQUIRED = "curriculum_required"
    VERSION_REQUIRED = "version_required"
    VERSION_NOT_FOUND = "version_not_found"
    ATS_ORIGINAL_REQUIRED = "ats_original_required"
    VACANCY_REQUIRED = "vacancy_required"
    SUCCESS = "success"


@dataclass(frozen=True)
class OptimizedResumeEvaluationRequest:
    """Minimal explicit request to evaluate a generated resume version."""

    application_id: int
    resume_version_id: int | None


@dataclass(frozen=True)
class OptimizedResumeEvaluationResult:
    """Immutable, non-persisted comparison between original and optimized ATS scores."""

    status: OptimizedResumeEvaluationStatus
    application_id: int
    curriculum_id: int | None = None
    resume_version_id: int | None = None
    original_score: float | None = None
    optimized_score: float | None = None
    score_delta: float | None = None
    comparison_state: str = "unknown"
    original_gaps: tuple[str, ...] = ()
    optimized_gaps: tuple[str, ...] = ()
    original_recommendations: tuple[str, ...] = ()
    optimized_recommendations: tuple[str, ...] = ()
    persisted: bool = False


class OptimizedResumeEvaluationUseCase:
    """Evaluate a selected generated version without changing persisted ATS history."""

    def __init__(
        self,
        application_context_service: ApplicationContextService,
        resume_context_service: ResumeContextService,
        version_query_port: GeneratedResumeVersionQueryPort,
        vacancy_query_port: VacancyQueryPort,
        ats_evaluator: ATSEvaluator,
    ) -> None:
        self._applications = application_context_service
        self._resumes = resume_context_service
        self._versions = version_query_port
        self._vacancies = vacancy_query_port
        self._ats_evaluator = ats_evaluator

    def execute(
        self,
        request: OptimizedResumeEvaluationRequest,
    ) -> OptimizedResumeEvaluationResult:
        """Return a transient ATS evaluation for the requested linked version."""
        application = self._applications.build(request.application_id)
        if application is None:
            return OptimizedResumeEvaluationResult(
                OptimizedResumeEvaluationStatus.APPLICATION_NOT_FOUND,
                request.application_id,
            )
        if application.curriculum_id is None or self._resumes.build(application.curriculum_id) is None:
            return OptimizedResumeEvaluationResult(
                OptimizedResumeEvaluationStatus.CURRICULUM_REQUIRED,
                request.application_id,
                application.curriculum_id,
            )
        if request.resume_version_id is None:
            return OptimizedResumeEvaluationResult(
                OptimizedResumeEvaluationStatus.VERSION_REQUIRED,
                request.application_id,
                application.curriculum_id,
            )

        version = next(
            (
                item
                for item in self._versions.list_by_curriculum_id(application.curriculum_id)
                if item.version_id == request.resume_version_id
            ),
            None,
        )
        if version is None:
            return OptimizedResumeEvaluationResult(
                OptimizedResumeEvaluationStatus.VERSION_NOT_FOUND,
                request.application_id,
                application.curriculum_id,
                request.resume_version_id,
            )

        original_ats = self._resumes.get_persisted_ats_result(application.curriculum_id)
        if original_ats is None:
            return OptimizedResumeEvaluationResult(
                OptimizedResumeEvaluationStatus.ATS_ORIGINAL_REQUIRED,
                request.application_id,
                application.curriculum_id,
                version.version_id,
            )
        vacancy = self._vacancies.get_by_id(application.job_id)
        if vacancy is None or not vacancy.competencies:
            return OptimizedResumeEvaluationResult(
                OptimizedResumeEvaluationStatus.VACANCY_REQUIRED,
                request.application_id,
                application.curriculum_id,
                version.version_id,
            )

        evaluation = self._ats_evaluator.evaluate(
            ATSEvaluationInput(
                resume_content=version.content,
                job_skills=vacancy.competencies,
                desired_skills=(),
                job_languages=(),
                job_certifications=(),
            )
        )
        original_score = original_ats.total_score
        optimized_score = evaluation.total_score
        score_delta = optimized_score - original_score
        return OptimizedResumeEvaluationResult(
            OptimizedResumeEvaluationStatus.SUCCESS,
            request.application_id,
            application.curriculum_id,
            version.version_id,
            original_score,
            optimized_score,
            score_delta,
            _comparison_state(score_delta),
            tuple(gap.skill_name for gap in original_ats.gaps or ()),
            evaluation.missing_skills,
            tuple(item.message for item in original_ats.recommendations or ()),
            evaluation.recommendations,
        )


def _comparison_state(score_delta: float | None) -> str:
    """Map a direct numeric delta to the supported comparison state."""
    if score_delta is None:
        return "unknown"
    if score_delta > 0:
        return "improved"
    if score_delta < 0:
        return "declined"
    return "unchanged"
