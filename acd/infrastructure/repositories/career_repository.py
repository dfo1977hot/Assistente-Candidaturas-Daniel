from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.career.career_goal import CareerGoal
from acd.domain.career.career_recommendation import CareerRecommendation
from acd.domain.career.development_plan import DevelopmentPlan
from acd.domain.career.milestone import Milestone
from acd.domain.career.skill_gap import CareerSkillGap


class CareerRepository:
    """Repository for career planning data persistence."""

    # Career Goals
    def create_goal(
        self,
        target_role: str,
        target_industry: str,
        deadline: datetime,
        *,
        target_location: str = "",
        target_salary: float = 0,
        target_work_model: str = "hybrid",
        priority: int = 1,
    ) -> CareerGoal:
        """Create a new career goal."""
        with database_module.SessionLocal() as session:
            goal = CareerGoal(
                target_role=target_role,
                target_industry=target_industry,
                target_location=target_location,
                target_salary=target_salary,
                target_work_model=target_work_model,
                deadline=deadline,
                priority=priority,
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)
            return goal

    def get_goal(self, goal_id: int) -> CareerGoal | None:
        """Retrieve a specific career goal."""
        with database_module.SessionLocal() as session:
            return session.scalar(select(CareerGoal).where(CareerGoal.id == goal_id))

    def list_goals(self, status: str = "active") -> list[CareerGoal]:
        """List all career goals with optional status filter."""
        with database_module.SessionLocal() as session:
            stmt = (
                select(CareerGoal).where(CareerGoal.status == status).order_by(CareerGoal.priority)
            )
            return list(session.scalars(stmt).all())

    def update_goal(self, goal_id: int, **kwargs) -> CareerGoal | None:
        """Update a career goal."""
        with database_module.SessionLocal() as session:
            goal = session.scalar(select(CareerGoal).where(CareerGoal.id == goal_id))
            if goal:
                for key, value in kwargs.items():
                    if hasattr(goal, key) and key != "id":
                        setattr(goal, key, value)
                goal.updated_at = datetime.now(UTC)
                session.commit()
                session.refresh(goal)
            return goal

    # Development Plans
    def create_plan(
        self,
        goal_id: int,
        title: str,
        start_date: datetime,
        target_date: datetime,
        *,
        actions: str = "[]",
        priority: int = 1,
    ) -> DevelopmentPlan:
        """Create a development plan."""
        with database_module.SessionLocal() as session:
            plan = DevelopmentPlan(
                goal_id=goal_id,
                title=title,
                actions=actions,
                priority=priority,
                start_date=start_date,
                target_date=target_date,
            )
            session.add(plan)
            session.commit()
            session.refresh(plan)
            return plan

    def get_plan(self, plan_id: int) -> DevelopmentPlan | None:
        """Retrieve a development plan."""
        with database_module.SessionLocal() as session:
            return session.scalar(select(DevelopmentPlan).where(DevelopmentPlan.id == plan_id))

    def list_plans_by_goal(self, goal_id: int) -> list[DevelopmentPlan]:
        """List all plans for a specific goal."""
        with database_module.SessionLocal() as session:
            stmt = select(DevelopmentPlan).where(DevelopmentPlan.goal_id == goal_id)
            return list(session.scalars(stmt).all())

    def update_plan_progress(self, plan_id: int, progress: int) -> DevelopmentPlan | None:
        """Update plan progress percentage."""
        with database_module.SessionLocal() as session:
            plan = session.scalar(select(DevelopmentPlan).where(DevelopmentPlan.id == plan_id))
            if plan:
                plan.progress = min(100, max(0, progress))
                plan.updated_at = datetime.now(UTC)
                session.commit()
                session.refresh(plan)
            return plan

    # Skill Gaps
    def create_gap(
        self,
        goal_id: int,
        skill_name: str,
        required_level: float,
        *,
        current_level: float = 0,
        gap_severity: str = "medium",
        estimated_hours: int = 40,
    ) -> CareerSkillGap:
        """Create a skill gap record."""
        with database_module.SessionLocal() as session:
            gap = CareerSkillGap(
                goal_id=goal_id,
                skill_name=skill_name,
                current_level=current_level,
                required_level=required_level,
                gap_severity=gap_severity,
                estimated_hours=estimated_hours,
            )
            session.add(gap)
            session.commit()
            session.refresh(gap)
            return gap

    def list_gaps_by_goal(self, goal_id: int) -> list[CareerSkillGap]:
        """List all skill gaps for a goal."""
        with database_module.SessionLocal() as session:
            stmt = (
                select(CareerSkillGap)
                .where(CareerSkillGap.goal_id == goal_id)
                .order_by(CareerSkillGap.priority)
            )
            return list(session.scalars(stmt).all())

    # Recommendations
    def create_recommendation(
        self,
        goal_id: int,
        title: str,
        category: str,
        impact: float,
        effort: float,
        *,
        description: str = "",
        estimated_duration_days: int = 30,
    ) -> CareerRecommendation:
        """Create a recommendation."""
        with database_module.SessionLocal() as session:
            rec = CareerRecommendation(
                goal_id=goal_id,
                title=title,
                description=description,
                category=category,
                impact=impact,
                effort=effort,
                estimated_duration_days=estimated_duration_days,
            )
            session.add(rec)
            session.commit()
            session.refresh(rec)
            return rec

    def list_recommendations_by_goal(self, goal_id: int) -> list[CareerRecommendation]:
        """List all recommendations for a goal."""
        with database_module.SessionLocal() as session:
            stmt = (
                select(CareerRecommendation)
                .where(CareerRecommendation.goal_id == goal_id)
                .order_by(CareerRecommendation.priority_score.desc())
            )
            return list(session.scalars(stmt).all())

    # Milestones
    def create_milestone(
        self,
        plan_id: int,
        title: str,
        target_date: datetime,
        order_index: int,
        *,
        description: str = "",
        success_criteria: str = "",
    ) -> Milestone:
        """Create a milestone."""
        with database_module.SessionLocal() as session:
            milestone = Milestone(
                plan_id=plan_id,
                title=title,
                description=description,
                target_date=target_date,
                order_index=order_index,
                success_criteria=success_criteria,
            )
            session.add(milestone)
            session.commit()
            session.refresh(milestone)
            return milestone

    def list_milestones_by_plan(self, plan_id: int) -> list[Milestone]:
        """List all milestones for a plan."""
        with database_module.SessionLocal() as session:
            stmt = (
                select(Milestone)
                .where(Milestone.plan_id == plan_id)
                .order_by(Milestone.order_index)
            )
            return list(session.scalars(stmt).all())

    def mark_milestone_complete(self, milestone_id: int) -> Milestone | None:
        """Mark a milestone as completed."""
        with database_module.SessionLocal() as session:
            milestone = session.scalar(select(Milestone).where(Milestone.id == milestone_id))
            if milestone:
                milestone.completed = True
                milestone.completed_date = datetime.now(UTC)
                session.commit()
                session.refresh(milestone)
            return milestone
