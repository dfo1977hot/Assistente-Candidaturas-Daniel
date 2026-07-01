from __future__ import annotations

from typing import Any

from acd.services.recommendation_engine import RecommendationEngine


def generate_recommendations(service: RecommendationEngine | None = None) -> list[dict[str, str]]:
    """Generate strategic recommendations based on analytics.
    
    Args:
        service: RecommendationEngine instance
        
    Returns:
        List of recommendation dictionaries
    """
    if service is None:
        service = RecommendationEngine()
    
    return service.generate_recommendations()
