from __future__ import annotations

from typing import Any

from acd.services.analytics_service import AnalyticsService


def generate_dashboard(service: AnalyticsService | None = None) -> dict[str, Any]:
    """Generate complete analytics dashboard.

    Args:
        service: AnalyticsService instance

    Returns:
        Dictionary containing dashboard data with KPIs, metrics, trends, and recommendations
    """
    if service is None:
        service = AnalyticsService()

    return service.generate_dashboard()
