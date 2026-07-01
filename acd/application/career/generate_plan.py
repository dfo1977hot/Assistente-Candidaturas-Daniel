from __future__ import annotations

from typing import Any

from acd.services.career_planning_service import CareerPlanningService


def generate_plan(
    goal_id: int,
    current_profile: dict[str, Any],
    *,
    service: CareerPlanningService | None = None,
) -> dict[str, Any]:
    """Generate development plan for a goal.
    
    Args:
        goal_id: Career goal ID
        current_profile: Current profile data
        service: CareerPlanningService instance
        
    Returns:
        Generated development plan with recommendations
    """
    if service is None:
        service = CareerPlanningService()

    return service.generate_development_plan(goal_id, current_profile)
