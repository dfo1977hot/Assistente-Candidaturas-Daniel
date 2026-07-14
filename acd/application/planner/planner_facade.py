from __future__ import annotations

from acd.domain.planner import (
    Analysis,
    PlannerResult,
)
from acd.services.planner import PlannerService


class PlannerFacade:
    """
    Camada de aplicação responsável por executar o Planner.

    A fachada coordena os serviços necessários para produzir
    um PlannerResult, sem conter regras de negócio.
    """

    def __init__(
        self,
        planner_service: PlannerService,
    ) -> None:
        """Inicializa a fachada do Planner."""

        self._planner_service = planner_service

    def analyze(
        self,
        analyses: list[Analysis],
    ) -> PlannerResult:
        """
        Executa o Planner.

        Parameters
        ----------
        analyses:
            Lista de análises utilizadas no planejamento.

        Returns
        -------
        PlannerResult
            Resultado consolidado do planejamento.
        """

        return self._planner_service.plan(analyses)