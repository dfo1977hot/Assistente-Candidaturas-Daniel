from __future__ import annotations

from acd.infrastructure.repositories.analytics_repository import AnalyticsRepository
from acd.services.metrics_engine import MetricsEngine


class RecommendationEngine:
    """Generates strategic recommendations based on analytics."""

    def __init__(
        self,
        repository: AnalyticsRepository | None = None,
        metrics_engine: MetricsEngine | None = None,
    ) -> None:
        self.repository = repository or AnalyticsRepository()
        self.metrics_engine = metrics_engine or MetricsEngine()

    def generate_recommendations(self) -> list[dict[str, str]]:
        """Generate recommendations based on current metrics."""
        recommendations = []
        metrics = self.metrics_engine.calculate_all_metrics()

        # ATS-based recommendation
        if metrics["ats"]["average_ats"] < 70:
            recommendations.append(
                {
                    "title": "Revisar formato do currículo",
                    "description": "Seu ATS médio está abaixo de 70. Considere revisar a estrutura do currículo.",
                    "priority": "high",
                    "action": "review_curriculum",
                }
            )

        # Conversion-based recommendation
        if metrics["conversion"]["conversion_interview_rate"] < 0.15:
            recommendations.append(
                {
                    "title": "Intensificar candidaturas",
                    "description": "A taxa de conversão para entrevistas está baixa. Aumente o volume de candidaturas.",
                    "priority": "high",
                    "action": "increase_applications",
                }
            )

        # Platform recommendation
        if "workday" in metrics["platforms"].get("best_platform", ""):
            recommendations.append(
                {
                    "title": "Priorizar Workday",
                    "description": "A plataforma Workday tem a melhor taxa de sucesso. Foque nela.",
                    "priority": "medium",
                    "action": "prioritize_platform",
                }
            )

        # Response time recommendation
        if metrics["time"]["avg_time_to_response"] > 5:
            recommendations.append(
                {
                    "title": "Acompanhar candidaturas ativas",
                    "description": "O tempo médio até resposta é alto. Realize follow-ups regularmente.",
                    "priority": "medium",
                    "action": "followup_applications",
                }
            )

        return recommendations

    def save_recommendations(self) -> None:
        """Generate and save recommendations."""
        recs = self.generate_recommendations()
        for rec in recs:
            self.repository.create_recommendation(
                title=rec["title"],
                description=rec["description"],
                priority=rec["priority"],
                action=rec["action"],
            )
