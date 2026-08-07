"""Presentation boundary for explicit resume optimization."""

from __future__ import annotations

from acd.application.resume_optimization.resume_optimization_use_case import (
    ResumeOptimizationRequest,
    ResumeOptimizationResult,
    ResumeOptimizationUseCase,
)
from acd.application.resume_optimization.resume_optimization_workflow import (
    ResumeOptimizationAvailability,
)
from acd.presentation.models.resume_optimization_view_state import ResumeOptimizationViewState


class ResumeOptimizationViewModel:
    """Map an explicit optimization request to a UI-safe immutable state."""

    _PRESENTATION = {
        ResumeOptimizationAvailability.APPLICATION_NOT_FOUND: ("Candidatura não encontrada", "A candidatura selecionada não está disponível."),
        ResumeOptimizationAvailability.CURRICULUM_REQUIRED: ("Currículo necessário", "Associe um currículo à candidatura antes de otimizar."),
        ResumeOptimizationAvailability.ATS_REQUIRED: ("Análise ATS necessária", "É necessária uma análise ATS persistida antes da otimização."),
        ResumeOptimizationAvailability.VACANCY_REQUIRED: ("Dados da vaga necessários", "A vaga não possui dados suficientes para otimizar o currículo."),
        ResumeOptimizationAvailability.READY: ("Currículo otimizado", "Uma nova versão foi criada e o currículo original foi preservado."),
    }

    def __init__(self, use_case: ResumeOptimizationUseCase) -> None:
        self._use_case = use_case

    def optimize(self, application_id: int) -> ResumeOptimizationViewState:
        """Execute one explicitly requested optimization."""
        return self._to_view_state(self._use_case.execute(ResumeOptimizationRequest(application_id)))

    def _to_view_state(self, result: ResumeOptimizationResult) -> ResumeOptimizationViewState:
        title, message = self._PRESENTATION[result.status]
        return ResumeOptimizationViewState(
            application_id=result.application_id,
            status=result.status.value,
            title=title,
            message=result.message or message,
            success=result.status is ResumeOptimizationAvailability.READY,
            version=result.version,
        )
