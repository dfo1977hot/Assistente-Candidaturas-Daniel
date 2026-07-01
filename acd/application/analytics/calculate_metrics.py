from __future__ import annotations

from typing import Any

from acd.services.analytics_service import AnalyticsService


def calculate_metrics(service: AnalyticsService | None = None) -> dict[str, Any]:
    """Calculate all metrics.
    
    Args:
        service: AnalyticsService instance
        
    Returns:
        Dictionary containing all calculated metrics
    """
    if service is None:
        service = AnalyticsService()
    
    return service.calculate_all_metrics()
