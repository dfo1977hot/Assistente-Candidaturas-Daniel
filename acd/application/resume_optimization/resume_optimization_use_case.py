"""Explicit command for persisted resume optimization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from acd.application.prompt.prompt_builder import PromptContext
from acd.application.resume_optimization.resume_optimization_workflow import (
    ResumeOptimizationAvailability,
    ResumeOptimizationWorkflow,
)


class ResumeOptimizationGenerator(Protocol):
    """Generates a new resume version from an already prepared prompt context."""

    def generate_resume_from_context(
        self, *, curriculum_id: int, context: PromptContext
    ) -> dict[str, str]: ...


@dataclass(frozen=True)
class ResumeOptimizationRequest:
    """Explicit user or authorized-consumer intent to optimize one application."""

    application_id: int


@dataclass(frozen=True)
class ResumeOptimizationResult:
    """Outcome of an explicit optimization command."""

    application_id: int
    status: ResumeOptimizationAvailability
    version: str | None = None
    message: str = ""


class ResumeOptimizationUseCase:
    """Execute generation only after an explicit request and ready persisted context."""

    def __init__(
        self,
        workflow: ResumeOptimizationWorkflow,
        generator: ResumeOptimizationGenerator,
    ) -> None:
        self._workflow = workflow
        self._generator = generator

    def execute(self, request: ResumeOptimizationRequest) -> ResumeOptimizationResult:
        """Generate a new version using persisted ATS context only."""
        preparation = self._workflow.execute(request.application_id)
        if preparation.availability is not ResumeOptimizationAvailability.READY:
            return ResumeOptimizationResult(request.application_id, preparation.availability)
        assert preparation.resume is not None
        assert preparation.ats_result is not None
        assert preparation.vacancy is not None
        assert preparation.curriculum_id is not None
        context = PromptContext(
            vacancy_title=preparation.vacancy.title,
            vacancy_description=preparation.vacancy.requirements or preparation.vacancy.notes,
            ats_score=preparation.ats_result.total_score,
            missing_skills=(
                None
                if preparation.gaps is None
                else [gap.skill_name for gap in preparation.gaps if gap.gap_type == "missing"]
            ),
            curriculum_summary=preparation.resume.description,
            professional_history=preparation.resume.description,
        )
        generated = self._generator.generate_resume_from_context(
            curriculum_id=preparation.curriculum_id,
            context=context,
        )
        return ResumeOptimizationResult(
            request.application_id,
            ResumeOptimizationAvailability.READY,
            version=generated.get("version"),
            message=generated.get("explanation", ""),
        )
