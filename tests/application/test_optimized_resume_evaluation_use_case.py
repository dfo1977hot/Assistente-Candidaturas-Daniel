"""Tests for transient optimized resume ATS evaluations."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from acd.application.composition.read_models import ApplicationContext, ResumeContext
from acd.application.optimized_resume_evaluation_use_case import (
    OptimizedResumeEvaluationRequest,
    OptimizedResumeEvaluationStatus,
    OptimizedResumeEvaluationUseCase,
    _comparison_state,
)
from acd.application.query_ports import (
    ATSGapQueryDTO,
    ATSHistoryQueryDTO,
    ATSRecommendationQueryDTO,
    GeneratedResumeVersionQueryDTO,
    VacancyQueryDTO,
)
from acd.domain.ats_evaluation import ATSEvaluationResult

_UNSET = object()


class _Applications:
    def __init__(self, application: ApplicationContext | None) -> None:
        self.application = application

    def build(self, application_id: int) -> ApplicationContext | None:
        return self.application if application_id == 1 else None


class _Resumes:
    def __init__(self, history: ATSHistoryQueryDTO | None = None) -> None:
        self.history = history
        self.original_evaluations = 0

    def build(self, curriculum_id: int) -> ResumeContext | None:
        return ResumeContext(curriculum_id, "v1", "currículo original")

    def get_persisted_ats_result(self, curriculum_id: int) -> ATSHistoryQueryDTO | None:
        return self.history


class _Versions:
    def __init__(self, versions: tuple[GeneratedResumeVersionQueryDTO, ...]) -> None:
        self.versions = versions

    def list_by_curriculum_id(
        self, curriculum_id: int
    ) -> tuple[GeneratedResumeVersionQueryDTO, ...]:
        return self.versions if curriculum_id == 10 else ()


class _Vacancies:
    def __init__(self, vacancy: VacancyQueryDTO | None) -> None:
        self.vacancy = vacancy

    def get_by_id(self, job_id: int) -> VacancyQueryDTO | None:
        return self.vacancy


class _Evaluator:
    def __init__(self, result: ATSEvaluationResult) -> None:
        self.result = result
        self.inputs = []

    def evaluate(self, evaluation_input):
        self.inputs.append(evaluation_input)
        return self.result


def _history() -> ATSHistoryQueryDTO:
    return ATSHistoryQueryDTO(
        score_id=1,
        curriculum_id=10,
        job_profile_id=2,
        total_score=60.0,
        calculated_at=datetime(2026, 1, 1, tzinfo=UTC),
        gaps=(ATSGapQueryDTO("Docker", "missing_skills"),),
        recommendations=(ATSRecommendationQueryDTO("Adicionar Docker", "gap"),),
    )


def _version(curriculum_id: int = 10) -> GeneratedResumeVersionQueryDTO:
    return GeneratedResumeVersionQueryDTO(
        version_id=7,
        curriculum_id=curriculum_id,
        version="v2",
        content="Python, SQL, Docker",
        explanation="Conteúdo otimizado",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _evaluation(score: float = 72.0) -> ATSEvaluationResult:
    return ATSEvaluationResult(score, (), ("Python",), ("Kubernetes",), (), ("Adicionar Kubernetes",))


def _use_case(
    *,
    application: ApplicationContext | None | object = _UNSET,
    history: ATSHistoryQueryDTO | None | object = _UNSET,
    versions: tuple[GeneratedResumeVersionQueryDTO, ...] | object = _UNSET,
    vacancy: VacancyQueryDTO | None | object = _UNSET,
) -> tuple[OptimizedResumeEvaluationUseCase, _Evaluator, _Resumes]:
    if application is _UNSET:
        application = ApplicationContext(1, 2, 3, "Draft", 10)
    if history is _UNSET:
        history = _history()
    if versions is _UNSET:
        versions = (_version(),)
    if vacancy is _UNSET:
        vacancy = VacancyQueryDTO(2, "Python", 3, "", competencies=("Python", "Docker"))
    evaluator = _Evaluator(_evaluation())
    resumes = _Resumes(history)
    return (
        OptimizedResumeEvaluationUseCase(
            _Applications(application),  # type: ignore[arg-type]
            resumes,  # type: ignore[arg-type]
            _Versions(versions),  # type: ignore[arg-type]
            _Vacancies(vacancy),  # type: ignore[arg-type]
            evaluator,  # type: ignore[arg-type]
        ),
        evaluator,
        resumes,
    )


def test_evaluates_only_selected_version_and_reuses_persisted_original_ats() -> None:
    use_case, evaluator, resumes = _use_case()

    result = use_case.execute(OptimizedResumeEvaluationRequest(1, 7))

    assert result.status is OptimizedResumeEvaluationStatus.SUCCESS
    assert result.original_score == 60.0
    assert result.optimized_score == 72.0
    assert result.score_delta == 12.0
    assert result.comparison_state == "improved"
    assert result.original_gaps == ("Docker",)
    assert result.persisted is False
    assert len(evaluator.inputs) == 1
    assert evaluator.inputs[0].resume_content == "Python, SQL, Docker"
    assert resumes.original_evaluations == 0


@pytest.mark.parametrize(
    ("evaluation_request", "application", "history", "versions", "vacancy", "status"),
    [
        (OptimizedResumeEvaluationRequest(99, 7), None, _history(), (_version(),), None, OptimizedResumeEvaluationStatus.APPLICATION_NOT_FOUND),
        (OptimizedResumeEvaluationRequest(1, None), ApplicationContext(1, 2, 3, "Draft", 10), _history(), (_version(),), None, OptimizedResumeEvaluationStatus.VERSION_REQUIRED),
        (OptimizedResumeEvaluationRequest(1, 8), ApplicationContext(1, 2, 3, "Draft", 10), _history(), (_version(),), None, OptimizedResumeEvaluationStatus.VERSION_NOT_FOUND),
        (OptimizedResumeEvaluationRequest(1, 7), ApplicationContext(1, 2, 3, "Draft", 10), None, (_version(),), None, OptimizedResumeEvaluationStatus.ATS_ORIGINAL_REQUIRED),
        (OptimizedResumeEvaluationRequest(1, 7), ApplicationContext(1, 2, 3, "Draft", 10), _history(), (_version(),), None, OptimizedResumeEvaluationStatus.VACANCY_REQUIRED),
    ],
)
def test_returns_preconditions_without_evaluating(
    evaluation_request: OptimizedResumeEvaluationRequest,
    application: ApplicationContext | None,
    history: ATSHistoryQueryDTO | None,
    versions: tuple[GeneratedResumeVersionQueryDTO, ...],
    vacancy: VacancyQueryDTO | None,
    status: OptimizedResumeEvaluationStatus,
) -> None:
    use_case, evaluator, _ = _use_case(
        application=application,
        history=history,
        versions=versions,
        vacancy=vacancy,
    )

    result = use_case.execute(evaluation_request)

    assert result.status is status
    assert evaluator.inputs == []
    assert result.persisted is False


@pytest.mark.parametrize(
    ("delta", "expected"),
    [(2.0, "improved"), (0.0, "unchanged"), (-2.0, "declined"), (None, "unknown")],
)
def test_comparison_state_is_direct_and_deterministic(delta: float | None, expected: str) -> None:
    assert _comparison_state(delta) == expected
