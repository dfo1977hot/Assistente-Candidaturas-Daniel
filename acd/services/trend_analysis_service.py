from __future__ import annotations

from typing import Any

from acd.infrastructure.repositories.analytics_repository import AnalyticsRepository
from acd.services.metrics_engine import MetricsEngine


class TrendAnalysisService:
    """Analyzes trends and patterns in metrics."""

    def __init__(self, repository: AnalyticsRepository | None = None, metrics_engine: MetricsEngine | None = None) -> None:
        self.repository = repository or AnalyticsRepository()
        self.metrics_engine = metrics_engine or MetricsEngine()

    def analyze_ats_trend(self) -> dict[str, Any]:
        """Analyze ATS trend over time."""
        trends = self.repository.get_trends("ats_average", dimension="global")
        if not trends:
            return {"trend": "stable", "direction": "neutral", "data_points": 0}

        values = [t.value for t in trends[-7:]]
        if len(values) < 2:
            return {"trend": "stable", "direction": "neutral", "data_points": len(values)}

        avg_recent = sum(values[-3:]) / 3 if len(values) >= 3 else values[-1]
        avg_previous = sum(values[:-3]) / (len(values) - 3) if len(values) > 3 else values[0]

        if avg_recent > avg_previous:
            direction = "up"
        elif avg_recent < avg_previous:
            direction = "down"
        else:
            direction = "stable"

        return {
            "trend": direction,
            "direction": direction,
            "data_points": len(values),
            "current_value": values[-1] if values else 0,
            "avg_previous": avg_previous,
            "avg_recent": avg_recent,
        }

    def analyze_conversion_trend(self) -> dict[str, Any]:
        """Analyze conversion rate trend."""
        trends = self.repository.get_trends("conversion_rate", dimension="global")
        if not trends:
            return {"trend": "stable", "direction": "neutral", "data_points": 0}

        values = [t.value for t in trends[-7:]]
        return {
            "trend": "stable" if len(values) < 2 else ("up" if values[-1] > values[0] else "down"),
            "direction": "stable" if len(values) < 2 else ("up" if values[-1] > values[0] else "down"),
            "data_points": len(values),
            "current_value": values[-1] if values else 0,
        }

    def record_metric_trend(self, metric_name: str, value: float, period: str = "daily", *, dimension: str = "global") -> None:
        """Record a metric value for trend tracking."""
        self.repository.create_trend(metric_name, value, period, dimension=dimension)

    def get_all_trends(self) -> dict[str, Any]:
        """Get all active trends."""
        return {
            "ats": self.analyze_ats_trend(),
            "conversion": self.analyze_conversion_trend(),
        }
