"""Persisted-data preparation workflow for resume optimization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from acd.application.composition.application_context_service import ApplicationContextService
from acd.application.composition.read_models import ResumeContext
from acd.application.composition.resume_context_service import ResumeContextService
from acd.application.query_ports import (
    ATSGapQueryDTO,
    ATSHistoryQueryDTO,
    ATSRecommendationQueryDTO,
    VacancyQueryDTO,
    VacancyQueryPort,
)


class ResumeOptimizationAvailability(StrEnum):
    """Availability states derived from persisted application data."""

    APPLICATION_NOT_FOUND = "application_not_found"
    CURRICULUM_REQUIRED = "curriculum_required"
    ATS_REQUIRED = "ats_required"
    VACANCY_REQUIRED = "vacancy_required"
    READY = "ready"


@dataclass(frozen=True)
class ResumeOptimizationPreparation:
    """Read-only persisted context required before an optimization is requested."""

    application_id: int
    curriculum_id: int | None
    availability: ResumeOptimizationAvailability
    resume: ResumeContext | None
    ats_result: ATSHistoryQueryDTO | None
    gaps: tuple[ATSGapQueryDTO, ...] | None
    recommendations: tuple[ATSRecommendationQueryDTO, ...] | None
    vacancy: VacancyQueryDTO | None


class ResumeOptimizationWorkflow:
    """Prepare optimization context without re-running ATS or recommendation analysis."""

    def __init__(
        self,
        application_context_service: ApplicationContextService,
        resume_context_service: ResumeContextService,
        vacancy_query_port: VacancyQueryPort,
    ) -> None:
        self._application_context_service = application_context_service
        self._resume_context_service = resume_context_service
        self._vacancy_query_port = vacancy_query_port

    def execute(self, application_id: int) -> ResumeOptimizationPreparation:
        """Load only persisted context associated with an application."""
        application = self._application_context_service.build(application_id)
        if application is None:
            return ResumeOptimizationPreparation(
                application_id, None, ResumeOptimizationAvailability.APPLICATION_NOT_FOUND,
                None, None, None, None, None,
            )
        if application.curriculum_id is None:
            return ResumeOptimizationPreparation(
                application_id, None, ResumeOptimizationAvailability.CURRICULUM_REQUIRED,
                None, None, None, None, None,
            )

        resume = self._resume_context_service.build(application.curriculum_id)
        if resume is None:
            return ResumeOptimizationPreparation(
                application_id,
                application.curriculum_id,
                ResumeOptimizationAvailability.CURRICULUM_REQUIRED,
                None, None,
                None,
                None,
                None,
            )
        ats_result = self._resume_context_service.get_persisted_ats_result(
            application.curriculum_id
        )
        if ats_result is None:
            return ResumeOptimizationPreparation(
                application_id, application.curriculum_id, ResumeOptimizationAvailability.ATS_REQUIRED,
                resume, None, None, None, None,
            )
        vacancy = self._vacancy_query_port.get_by_id(application.job_id)
        if vacancy is None or not (vacancy.requirements or vacancy.notes):
            return ResumeOptimizationPreparation(
                application_id,
                application.curriculum_id,
                ResumeOptimizationAvailability.VACANCY_REQUIRED,
                resume,
                ats_result,
                ats_result.gaps,
                ats_result.recommendations,
                None,
            )
        return ResumeOptimizationPreparation(
            application_id, application.curriculum_id, ResumeOptimizationAvailability.READY,
            resume, ats_result, ats_result.gaps, ats_result.recommendations, vacancy,
        )
