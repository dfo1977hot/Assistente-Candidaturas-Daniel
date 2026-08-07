from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from acd.infrastructure.career.recommendation_engine import RecommendationRankingEngine
from acd.infrastructure.career.rule_engine import CareerRuleEngine
from acd.infrastructure.repositories.career_repository import CareerRepository


class CareerPlanningService:
    """Main service for career planning orchestration."""

    def __init__(
        self,
        repository: CareerRepository | None = None,
        rule_engine: CareerRuleEngine | None = None,
        recommendation_engine: RecommendationRankingEngine | None = None,
    ) -> None:
        self.repository = repository or CareerRepository()
        self.rule_engine = rule_engine or CareerRuleEngine()
        self.recommendation_engine = recommendation_engine or RecommendationRankingEngine(
            self.rule_engine
        )

    def create_career_goal(
        self,
        target_role: str,
        target_industry: str,
        deadline_months: int,
        *,
        target_location: str = "",
        target_salary: float = 0,
        target_work_model: str = "hybrid",
        priority: int = 1,
    ) -> dict[str, Any]:
        """Create a new career goal.

        Args:
            target_role: Target position title
            target_industry: Target industry
            deadline_months: Months until deadline
            target_location: Desired location
            target_salary: Target salary
            target_work_model: Work arrangement (onsite, hybrid, remote)
            priority: Goal priority (1-10)

        Returns:
            Created goal data
        """
        deadline = datetime.now(UTC) + timedelta(days=deadline_months * 30)

        goal = self.repository.create_goal(
            target_role=target_role,
            target_industry=target_industry,
            target_location=target_location,
            target_salary=target_salary,
            target_work_model=target_work_model,
            deadline=deadline,
            priority=priority,
        )

        return {
            "id": goal.id,
            "target_role": goal.target_role,
            "target_industry": goal.target_industry,
            "deadline": goal.deadline.isoformat(),
            "priority": goal.priority,
        }

    def get_goal_details(self, goal_id: int) -> dict[str, Any]:
        """Get detailed goal information."""
        goal = self.repository.get_goal(goal_id)
        if not goal:
            return {}

        return {
            "id": goal.id,
            "target_role": goal.target_role,
            "target_industry": goal.target_industry,
            "target_location": goal.target_location,
            "target_salary": float(goal.target_salary),
            "target_work_model": goal.target_work_model,
            "deadline": goal.deadline.isoformat(),
            "priority": goal.priority,
            "current_compatibility": float(goal.current_compatibility),
            "status": goal.status,
            "created_at": goal.created_at.isoformat(),
        }

    def list_active_goals(self) -> list[dict[str, Any]]:
        """List all active career goals."""
        goals = self.repository.list_goals(status="active")
        return [
            {
                "id": g.id,
                "target_role": g.target_role,
                "compatibility": float(g.current_compatibility),
                "priority": g.priority,
                "deadline": g.deadline.isoformat(),
            }
            for g in goals
        ]

    def generate_development_plan(
        self, goal_id: int, current_profile: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate development plan for a goal.

        Args:
            goal_id: Career goal ID
            current_profile: Current skills, certifications, languages

        Returns:
            Generated development plan
        """
        goal = self.repository.get_goal(goal_id)
        if not goal:
            return {}

        # Analyze compatibility
        analysis = self.rule_engine.analyze_compatibility(current_profile, goal.target_role)

        # Update goal compatibility
        self.repository.update_goal(goal_id, current_compatibility=analysis["compatibility"])

        # Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(
            {
                "target_role": goal.target_role,
                "target_industry": goal.target_industry,
            },
            analysis["gaps"],
        )

        # Create development plan
        now = datetime.now(UTC) 
        plan = self.repository.create_plan(
            goal_id=goal_id,
            title=f"Plano para {goal.target_role}",
            start_date=now,
            target_date=goal.deadline,
        )

        # Create milestones from development path
        dev_path = self.rule_engine.generate_development_path(analysis["gaps"])
        for idx, step in enumerate(dev_path, 1):
            milestone_date = now + timedelta(days=step.get("estimated_hours", 40) // 8 * 5)
            self.repository.create_milestone(
                plan_id=plan.id,
                title=f"Dominar {step['skill']}",
                target_date=milestone_date,
                order_index=idx,
                success_criteria=f"Atingir nível {step['target']} em {step['skill']}",
            )

        return {
            "plan_id": plan.id,
            "goal_id": goal_id,
            "compatibility": analysis["compatibility"],
            "gaps": analysis["gaps"],
            "strengths": analysis["strengths"],
            "recommendations_count": len(recommendations),
            "recommendations": recommendations[:5],  # Top 5 recommendations
        }

    def update_goal_progress(self, goal_id: int, progress_percentage: int) -> dict[str, Any]:
        """Update progress on a goal."""
        goal = self.repository.update_goal(goal_id, progress=progress_percentage)
        if goal:
            return {"goal_id": goal_id, "progress": goal.progress}
        return {}

    def get_statistics(self) -> dict[str, Any]:
        """Get career planning statistics."""
        goals = self.repository.list_goals()

        if not goals:
            return {
                "active_goals": 0,
                "average_compatibility": 0,
                "total_gaps": 0,
            }

        return {
            "active_goals": len(goals),
            "average_compatibility": sum(float(g.current_compatibility) for g in goals)
            / len(goals),
            "goals_by_priority": {
                "high": len([g for g in goals if g.priority <= 3]),
                "medium": len([g for g in goals if 3 < g.priority <= 6]),
                "low": len([g for g in goals if g.priority > 6]),
            },
        }
