from __future__ import annotations

from acd.domain.planner.recommendation import Recommendation


class RecommendationEngine:
    """
    Gera recomendações baseadas no score consolidado.
    """

    def generate(
        self,
        overall_score: float,
    ) -> list[Recommendation]:

        recommendations: list[Recommendation] = []

        if overall_score >= 90:
            recommendations.append(
                Recommendation(
                    title="Aplicar imediatamente",
                    description="A vaga possui excelente aderência.",
                )
            )

        elif overall_score >= 75:
            recommendations.append(
                Recommendation(
                    title="Adaptar currículo",
                    description="Pequenos ajustes podem aumentar a aderência.",
                )
            )

        else:
            recommendations.append(
                Recommendation(
                    title="Baixa prioridade",
                    description="Considere investir seu tempo em outras vagas.",
                )
            )

        return recommendations
