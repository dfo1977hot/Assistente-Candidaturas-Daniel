from __future__ import annotations

from acd.domain.planner.analysis import Analysis


class PlannerScoreEngine:
    """
    Responsável pelo cálculo da pontuação consolidada do Planner.
    """

    def calculate_overall_score(
        self,
        analyses: list[Analysis],
    ) -> float:
        """
        Calcula a média ponderada das análises.

        Retorna um valor entre 0 e 100.
        """

        if not analyses:
            return 0.0

        total_weight = sum(analysis.weight for analysis in analyses)

        if total_weight == 0:
            return 0.0

        weighted_sum = sum(analysis.score * analysis.weight for analysis in analyses)

        return round(
            weighted_sum / total_weight,
            2,
        )
