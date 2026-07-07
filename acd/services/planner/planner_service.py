from __future__ import annotations

from acd.domain.planner import (
    Analysis,
    PlannerResult,
)

from .engines import (
    PlannerScoreEngine,
    RecommendationEngine,
    StrategyEngine,
)


class PlannerService:
    """
    Serviço responsável por orquestrar o processo de planejamento.

    O PlannerService coordena os Engines do Planner, mas não contém
    regras de negócio. Cada decisão é delegada a um Engine
    especializado.
    """

    def __init__(self) -> None:
        self._score_engine = PlannerScoreEngine()
        self._recommendation_engine = RecommendationEngine()
        self._strategy_engine = StrategyEngine()

    def plan(
        self,
        analyses: list[Analysis],
    ) -> PlannerResult:
        """
        Executa o processo completo de planejamento.

        Parameters
        ----------
        analyses:
            Lista de análises realizadas sobre a vaga.

        Returns
        -------
        PlannerResult
            Resultado consolidado do planejamento.
        """

        overall_score = self._score_engine.calculate_overall_score(analyses)

        recommendations = self._recommendation_engine.generate(overall_score)

        strategy = self._strategy_engine.determine(overall_score)

        result = PlannerResult()

        result.overall_score = overall_score
        result.recommendations = recommendations
        result.strategy = strategy

        return result
