from __future__ import annotations

from typing import Any

from acd.services.career_planning_service import CareerPlanningService
from acd.services.gap_analysis_service import GapAnalysisService


def evaluate_goal(
    goal_id: int,
    current_profile: dict[str, Any],
    *,
    planning_service: CareerPlanningService | None = None,
    gap_service: GapAnalysisService | None = None,
) -> dict[str, Any]:
    """Evaluate a career goal against current profile.
    
    Args:
        goal_id: Career goal ID
        current_profile: Current skills, certifications, languages
        planning_service: CareerPlanningService instance
        gap_service: GapAnalysisService instance
        
    Returns:
        Goal evaluation with gaps and recommendations
    """
    if planning_service is None:
        planning_service = CareerPlanningService()
    if gap_service is None:
        gap_service = GapAnalysisService()

    gap_analysis = gap_service.analyze_goal(goal_id, current_profile)
    goal_details = planning_service.get_goal_details(goal_id)

    return {
        "goal": goal_details,
        "analysis": gap_analysis,
        "timeline": gap_service.estimate_timeline(goal_id),
    }
