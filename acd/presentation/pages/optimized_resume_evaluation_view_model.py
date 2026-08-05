"""Presentation mapping for explicit transient optimized resume evaluations."""

from __future__ import annotations

from acd.application.optimized_resume_evaluation_use_case import (
    OptimizedResumeEvaluationRequest,
    OptimizedResumeEvaluationResult,
    OptimizedResumeEvaluationStatus,
    OptimizedResumeEvaluationUseCase,
)
from acd.presentation.models.optimized_resume_evaluation_view_state import (
    OptimizedResumeEvaluationViewState,
)


class OptimizedResumeEvaluationViewModel:
    """Create requests and map transient Application results for Presentation."""

    _MESSAGES: dict[OptimizedResumeEvaluationStatus, tuple[str, str]] = {
        OptimizedResumeEvaluationStatus.APPLICATION_NOT_FOUND: (
            "Candidatura não encontrada",
            "A candidatura selecionada não está disponível.",
        ),
        OptimizedResumeEvaluationStatus.CURRICULUM_REQUIRED: (
            "Currículo necessário",
            "Associe um currículo à candidatura antes de avaliar uma versão.",
        ),
        OptimizedResumeEvaluationStatus.VERSION_REQUIRED: (
            "Versão necessária",
            "Selecione uma versão otimizada para avaliar.",
        ),
        OptimizedResumeEvaluationStatus.VERSION_NOT_FOUND: (
            "Versão não encontrada",
            "A versão selecionada não pertence a este currículo.",
        ),
        OptimizedResumeEvaluationStatus.ATS_ORIGINAL_REQUIRED: (
            "ATS original necessário",
            "Não há uma avaliação ATS original persistida para comparação.",
        ),
        OptimizedResumeEvaluationStatus.VACANCY_REQUIRED: (
            "Contexto da vaga necessário",
            "A vaga não possui competências estruturadas para avaliação.",
        ),
        OptimizedResumeEvaluationStatus.SUCCESS: (
            "Avaliação atual da versão selecionada",
            "Este resultado não foi salvo no histórico.",
        ),
    }

    def __init__(self, use_case: OptimizedResumeEvaluationUseCase) -> None:
        self._use_case = use_case

    def evaluate(
        self,
        application_id: int,
        resume_version_id: int | None,
    ) -> OptimizedResumeEvaluationViewState:
        """Execute one explicit evaluation for the captured visual context."""
        return self._map(
            self._use_case.execute(
                OptimizedResumeEvaluationRequest(application_id, resume_version_id)
            )
        )

    def _map(
        self,
        result: OptimizedResumeEvaluationResult,
    ) -> OptimizedResumeEvaluationViewState:
        title, message = self._MESSAGES[result.status]
        return OptimizedResumeEvaluationViewState(
            status=result.status.value,
            title=title,
            message=message,
            application_id=result.application_id,
            resume_version_id=result.resume_version_id,
            original_score=result.original_score,
            optimized_score=result.optimized_score,
            score_delta=result.score_delta,
            comparison_state=result.comparison_state,
            original_gaps=result.original_gaps,
            optimized_gaps=result.optimized_gaps,
            original_recommendations=result.original_recommendations,
            optimized_recommendations=result.optimized_recommendations,
            persisted=result.persisted,
        )
