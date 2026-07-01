from __future__ import annotations

from typing import Any

from acd.infrastructure.repositories.career_repository import CareerRepository
from acd.infrastructure.career.rule_engine import CareerRuleEngine


class GapAnalysisService:
    """Service for analyzing skill gaps between current and target roles."""

    def __init__(self, repository: CareerRepository | None = None, rule_engine: CareerRuleEngine | None = None) -> None:
        self.repository = repository or CareerRepository()
        self.rule_engine = rule_engine or CareerRuleEngine()

    def analyze_goal(self, goal_id: int, current_profile: dict[str, Any]) -> dict[str, Any]:
        """Analyze gaps for a specific goal.
        
        Args:
            goal_id: Career goal ID
            current_profile: Current profile data
            
        Returns:
            Comprehensive gap analysis
        """
        goal = self.repository.get_goal(goal_id)
        if not goal:
            return {}

        analysis = self.rule_engine.analyze_compatibility(current_profile, goal.target_role)

        # Store gaps in database
        for gap in analysis["gaps"]:
            self.repository.create_gap(
                goal_id=goal_id,
                skill_name=gap["skill"],
                current_level=gap["current"],
                required_level=gap["required"],
                gap_severity=gap["severity"],
                estimated_hours=self.rule_engine._estimate_learning_hours(gap["required"] - gap["current"]),
            )

        return {
            "goal_id": goal_id,
            "target_role": goal.target_role,
            "compatibility": analysis["compatibility"],
            "gaps_count": len(analysis["gaps"]),
            "critical_gaps": len([g for g in analysis["gaps"] if g["severity"] == "critical"]),
            "high_gaps": len([g for g in analysis["gaps"] if g["severity"] == "high"]),
            "gaps": analysis["gaps"],
            "strengths": analysis["strengths"],
            "certificates_missing": analysis.get("certificates_missing", []),
        }

    def get_gap_details(self, goal_id: int) -> dict[str, Any]:
        """Get detailed gap information for a goal."""
        gaps = self.repository.list_gaps_by_goal(goal_id)

        if not gaps:
            return {"gaps": [], "total_estimated_hours": 0}

        total_hours = sum(g.estimated_hours for g in gaps)
        gap_data = [
            {
                "skill": g.skill_name,
                "current_level": float(g.current_level),
                "required_level": float(g.required_level),
                "severity": g.gap_severity,
                "estimated_hours": g.estimated_hours,
                "priority": g.priority,
            }
            for g in gaps
        ]

        return {
            "gaps": gap_data,
            "total_gaps": len(gaps),
            "total_estimated_hours": total_hours,
            "estimated_weeks": total_hours // 40,
        }

    def get_learning_path(self, goal_id: int) -> list[dict[str, Any]]:
        """Get ordered learning path for goal.
        
        Returns steps in recommended order based on severity and dependencies.
        """
        gaps = self.repository.list_gaps_by_goal(goal_id)
        gap_dicts = [
            {
                "skill": g.skill_name,
                "current": float(g.current_level),
                "required": float(g.required_level),
                "severity": g.gap_severity,
                "estimated_hours": g.estimated_hours,
            }
            for g in gaps
        ]

        return self.rule_engine.generate_development_path(gap_dicts)

    def estimate_timeline(self, goal_id: int) -> dict[str, Any]:
        """Estimate timeline to close all gaps.
        
        Returns timeline estimate based on hours and daily learning capacity.
        """
        gaps = self.repository.list_gaps_by_goal(goal_id)

        if not gaps:
            return {"estimated_days": 0, "estimated_weeks": 0, "estimated_months": 0}

        total_hours = sum(g.estimated_hours for g in gaps)

        # Assuming 5 hours per week of dedicated learning
        weeks = total_hours / 5
        days = weeks * 7
        months = days / 30

        return {
            "total_hours": total_hours,
            "estimated_days": int(days),
            "estimated_weeks": int(weeks),
            "estimated_months": int(months),
            "aggressive_schedule_weeks": int(weeks / 2),  # 10 hours per week
        }
