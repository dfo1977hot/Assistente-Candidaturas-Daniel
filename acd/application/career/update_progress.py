from __future__ import annotations

from typing import Any

from acd.services.career_planning_service import CareerPlanningService


def update_progress(
    goal_id: int,
    progress_percentage: int,
    *,
    service: CareerPlanningService | None = None,
) -> dict[str, Any]:
    """Update progress on a career goal.

    Args:
        goal_id: Career goal ID
        progress_percentage: Progress percentage (0-100)
        service: CareerPlanningService instance

    Returns:
        Updated progress data
    """
    if service is None:
        service = CareerPlanningService()

    return service.update_goal_progress(goal_id, progress_percentage)
