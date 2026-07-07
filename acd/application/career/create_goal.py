from __future__ import annotations

from typing import Any

from acd.services.career_planning_service import CareerPlanningService


def create_goal(
    target_role: str,
    target_industry: str,
    deadline_months: int,
    *,
    service: CareerPlanningService | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create a new career goal.

    Args:
        target_role: Target position title
        target_industry: Target industry
        deadline_months: Months to achieve goal
        service: CareerPlanningService instance
        **kwargs: Additional goal parameters

    Returns:
        Created goal data
    """
    if service is None:
        service = CareerPlanningService()

    return service.create_career_goal(
        target_role=target_role,
        target_industry=target_industry,
        deadline_months=deadline_months,
        **kwargs,
    )
