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

    def __init__(self) -> None:
        self._planner_service = PlannerService()

    def analyze(
        self,
        analyses: list[Analysis],
    ) -> PlannerResult:
        """
        Executa o Planner.
        """

        return self._planner_service.plan(analyses)
