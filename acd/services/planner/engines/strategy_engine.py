from __future__ import annotations

from acd.domain.planner.enums import StrategyType


class StrategyEngine:
    """
    Determina a estratégia ideal para a candidatura.
    """

    def determine(
        self,
        overall_score: float,
    ) -> StrategyType:

        if overall_score >= 90:
            return StrategyType.APPLY_NOW

        if overall_score >= 75:
            return StrategyType.ADAPT_RESUME

        if overall_score >= 60:
            return StrategyType.ADAPT_RESUME_AND_COVER

        return StrategyType.LOW_PRIORITY
