from __future__ import annotations

import json
from typing import Any

from acd.infrastructure.repositories.analytics_repository import AnalyticsRepository
from acd.services.metrics_engine import MetricsEngine
from acd.services.recommendation_engine import RecommendationEngine
from acd.services.trend_analysis_service import TrendAnalysisService


class AnalyticsService:
    """Main analytics service orchestrating all analytics operations."""

    def __init__(
        self,
        repository: AnalyticsRepository | None = None,
        metrics_engine: MetricsEngine | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        trend_service: TrendAnalysisService | None = None,
    ) -> None:
        self.repository = repository or AnalyticsRepository()
        self.metrics_engine = metrics_engine or MetricsEngine()
        self.recommendation_engine = recommendation_engine or RecommendationEngine(self.repository, self.metrics_engine)
        self.trend_service = trend_service or TrendAnalysisService(self.repository, self.metrics_engine)

    def calculate_kpis(self) -> dict[str, Any]:
        """Calculate all KPIs for dashboard."""
        metrics = self.metrics_engine.calculate_all_metrics()
        return {
            "conversion_to_interview": f"{metrics['conversion']['conversion_interview_rate']*100:.1f}%",
            "average_ats": f"{metrics['ats']['average_ats']:.1f}",
            "best_platform": metrics["platforms"].get("best_platform", "N/A"),
            "total_applications": metrics["conversion"]["applications"],
            "interviews_scheduled": metrics["conversion"]["interviews"],
            "offers_received": metrics["conversion"]["offers"],
        }

    def generate_dashboard(self) -> dict[str, Any]:
        """Generate complete dashboard data."""
        return {
            "kpis": self.calculate_kpis(),
            "metrics": self.metrics_engine.calculate_all_metrics(),
            "trends": self.trend_service.get_all_trends(),
            "recommendations": self.recommendation_engine.generate_recommendations(),
        }

    def get_conversion_funnel(self) -> list[dict[str, Any]]:
        """Get conversion funnel data for visualization."""
        metrics = self.metrics_engine.calculate_conversion_metrics()
        return [
            {"stage": "Jobs Found", "count": metrics["jobs_found"]},
            {"stage": "Applications", "count": metrics["applications"]},
            {"stage": "Interviews", "count": metrics["interviews"]},
            {"stage": "Offers", "count": metrics["offers"]},
            {"stage": "Hired", "count": metrics["hired"]},
        ]

    def get_recommendations(self) -> list[dict[str, Any]]:
        """Get current recommendations."""
        return self.recommendation_engine.generate_recommendations()

    def create_snapshot(self, period: str = "daily") -> dict[str, Any]:
        """Create a metrics snapshot for historical tracking."""
        dashboard = self.generate_dashboard()
        summary = json.dumps(dashboard["kpis"])
        kpis = json.dumps(dashboard["kpis"])
        snapshot = self.repository.create_snapshot(period, summary, kpis)
        return {"id": snapshot.id, "period": snapshot.period, "created_at": str(snapshot.created_at)}
