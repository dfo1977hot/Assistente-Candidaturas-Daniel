"""Tests for the explicit persisted resume optimization command."""

from __future__ import annotations

from datetime import UTC, datetime

from acd.application.composition.read_models import ResumeContext
from acd.application.prompt.prompt_builder import PromptContext
from acd.application.query_ports import ATSHistoryQueryDTO, VacancyQueryDTO
from acd.application.resume_optimization.resume_optimization_use_case import (
    ResumeOptimizationRequest,
    ResumeOptimizationUseCase,
)
from acd.application.resume_optimization.resume_optimization_workflow import (
    ResumeOptimizationAvailability,
    ResumeOptimizationPreparation,
)


class _Workflow:
    def __init__(self, preparation: ResumeOptimizationPreparation) -> None:
        self.preparation = preparation
        self.requests: list[int] = []

    def execute(self, application_id: int) -> ResumeOptimizationPreparation:
        self.requests.append(application_id)
        return self.preparation


class _Generator:
    def __init__(self) -> None:
        self.calls: list[tuple[int, PromptContext]] = []

    def generate_resume_from_context(
        self, *, curriculum_id: int, context: PromptContext
    ) -> dict[str, str]:
        self.calls.append((curriculum_id, context))
        return {"content": "optimized", "version": "v2.0", "explanation": "persisted"}


def _preparation(
    availability: ResumeOptimizationAvailability = ResumeOptimizationAvailability.READY,
) -> ResumeOptimizationPreparation:
    return ResumeOptimizationPreparation(
        application_id=1,
        curriculum_id=4,
        availability=availability,
        resume=ResumeContext(4, "v1", "Python developer"),
        ats_result=ATSHistoryQueryDTO(1, 4, None, 80.0, datetime(2026, 7, 26, tzinfo=UTC)),
        gaps=None,
        recommendations=None,
        vacancy=VacancyQueryDTO(2, "Backend Engineer", 3, "Remote", requirements="Python and Docker"),
    )


def test_use_case_generates_only_for_an_explicit_ready_request() -> None:
    workflow = _Workflow(_preparation())
    generator = _Generator()

    result = ResumeOptimizationUseCase(workflow, generator).execute(ResumeOptimizationRequest(1))

    assert workflow.requests == [1]
    assert result.status is ResumeOptimizationAvailability.READY
    assert result.version == "v2.0"
    assert generator.calls == [(4, generator.calls[0][1])]
    context = generator.calls[0][1]
    assert context.vacancy_title == "Backend Engineer"
    assert context.vacancy_description == "Python and Docker"
    assert context.ats_score == 80.0
    assert context.missing_skills is None


def test_use_case_does_not_call_generation_when_a_prerequisite_is_missing() -> None:
    workflow = _Workflow(_preparation(ResumeOptimizationAvailability.ATS_REQUIRED))
    generator = _Generator()

    result = ResumeOptimizationUseCase(workflow, generator).execute(ResumeOptimizationRequest(1))

    assert result.status is ResumeOptimizationAvailability.ATS_REQUIRED
    assert generator.calls == []
