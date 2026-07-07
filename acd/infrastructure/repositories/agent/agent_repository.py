from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from datetime import UTC, datetime
from acd.database import database as database_module
from acd.domain.agent.agent_goal import AgentGoal
from acd.domain.agent.execution_plan import ExecutionPlan
from acd.domain.agent.reasoning_step import ReasoningStep
from acd.domain.agent.tool_call import ToolCall

if TYPE_CHECKING:
    from acd.domain.agents.memory import AgentMemory
    from acd.domain.agent.plan_task import PlanTask


class AgentRepository:
    """Repository for agent data persistence."""

    # Goals
    def create_goal(
        self,
        title: str,
        description: str,
        objective_type: str,
        *,
        priority: int = 1,
    ) -> AgentGoal:
        """Create a new agent goal."""
        with database_module.SessionLocal() as session:
            goal = AgentGoal(
                title=title,
                description=description,
                objective_type=objective_type,
                priority=priority,
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)
            return goal

    def get_goal(self, goal_id: int) -> AgentGoal | None:
        """Get goal by ID."""
        with database_module.SessionLocal() as session:
            stmt = select(AgentGoal).where(AgentGoal.id == goal_id)
            return session.scalar(stmt)

    def list_goals(self, status: str = "pending", limit: int = 10) -> list[AgentGoal]:
        """List goals by status."""
        with database_module.SessionLocal() as session:
            stmt = select(AgentGoal).where(AgentGoal.status == status).limit(limit)
            return list(session.scalars(stmt).all())

    def update_goal(self, goal_id: int, **kwargs: Any) -> AgentGoal | None:
        """Update goal."""
        with database_module.SessionLocal() as session:
            goal = session.get(AgentGoal, goal_id)
            if goal:
                for key, value in kwargs.items():
                    if hasattr(goal, key):
                        setattr(goal, key, value)
                session.commit()
                session.refresh(goal)
            return goal

    # Execution Plans
    def create_plan(
        self,
        goal_id: int,
        title: str,
        description: str,
        strategy: str,
        estimated_duration_seconds: int,
    ) -> ExecutionPlan:
        """Create an execution plan."""
        with database_module.SessionLocal() as session:
            plan = ExecutionPlan(
                goal_id=goal_id,
                title=title,
                description=description,
                strategy=strategy,
                estimated_duration_seconds=estimated_duration_seconds,
            )
            session.add(plan)
            session.commit()
            session.refresh(plan)
            return plan

    def get_plan(self, plan_id: int) -> ExecutionPlan | None:
        """Get plan by ID."""
        with database_module.SessionLocal() as session:
            return session.get(ExecutionPlan, plan_id)

    def list_plans_by_goal(self, goal_id: int) -> list[ExecutionPlan]:
        """List all plans for a goal."""
        with database_module.SessionLocal() as session:
            stmt = select(ExecutionPlan).where(ExecutionPlan.goal_id == goal_id)
            return list(session.scalars(stmt).all())

    def update_plan(self, plan_id: int, **kwargs: Any) -> ExecutionPlan | None:
        """Update plan."""
        with database_module.SessionLocal() as session:
            plan = session.get(ExecutionPlan, plan_id)
            if plan:
                for key, value in kwargs.items():
                    if hasattr(plan, key):
                        setattr(plan, key, value)
                session.commit()
                session.refresh(plan)
            return plan

    def approve_plan(self, plan_id: int, approved: bool = True) -> ExecutionPlan | None:
        """Approve or reject plan."""
        from datetime import datetime

        return self.update_plan(
            plan_id,
            approval_status="approved" if approved else "rejected",
            approved_by_user=approved,
            approved_at=datetime.now(UTC) if approved else None,
        )

    # Tasks
    def create_task(
        self,
        plan_id: int,
        task_type: str,
        description: str,
        tool_name: str,
        order_index: int,
        **kwargs: Any,
    ) -> PlanTask:
        """Create a task in a plan."""
        from acd.domain.agent.plan_task import PlanTask

        with database_module.SessionLocal() as session:
            task = PlanTask(
                plan_id=plan_id,
                task_type=task_type,
                description=description,
                tool_name=tool_name,
                order_index=order_index,
                **{k: v for k, v in kwargs.items() if hasattr(PlanTask, k)},
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    def get_task(self, task_id: int) -> PlanTask | None:
        """Get task by ID."""
        from acd.domain.agent.plan_task import PlanTask

        with database_module.SessionLocal() as session:
            return session.get(PlanTask, task_id)

    def list_tasks_by_plan(self, plan_id: int) -> list[PlanTask]:
        """List all tasks in a plan."""
        from acd.domain.agent.plan_task import PlanTask

        with database_module.SessionLocal() as session:
            stmt = select(PlanTask).where(PlanTask.plan_id == plan_id).order_by(PlanTask.order_index)
            return list(session.scalars(stmt).all())

    def update_task(self, task_id: int, **kwargs: Any) -> PlanTask | None:
        """Update task."""
        from acd.domain.agent.plan_task import PlanTask

        with database_module.SessionLocal() as session:
            task = session.get(PlanTask, task_id)
            if task:
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                session.commit()
                session.refresh(task)
            return task

    # Memory
    def save_memory(
        self,
        memory_type: str,
        key: str,
        value: str,
        *,
        context: str = "",
        importance: int = 1,
    ) -> AgentMemory:
        """Save to agent memory."""
        from acd.domain.agents.memory import AgentMemory

        with database_module.SessionLocal() as session:
            memory = AgentMemory(
                memory_type=memory_type,
                key=key,
                value=value,
                context=context,
                importance=importance,
            )
            session.add(memory)
            session.commit()
            session.refresh(memory)
            return memory

    def get_memory(self, key: str) -> AgentMemory | None:
        """Retrieve memory by key."""
        from acd.domain.agents.memory import AgentMemory

        with database_module.SessionLocal() as session:
            stmt = select(AgentMemory).where(AgentMemory.key == key)
            return session.scalar(stmt)

    def list_memory_by_type(self, memory_type: str, limit: int = 50) -> list[AgentMemory]:
        """List memory entries by type."""
        from acd.domain.agents.memory import AgentMemory

        with database_module.SessionLocal() as session:
            stmt = (
                select(AgentMemory)
                .where(AgentMemory.memory_type == memory_type)
                .order_by(AgentMemory.updated_at.desc())
                .limit(limit)
            )
            return list(session.scalars(stmt).all())

    # Reasoning Steps
    def save_reasoning_step(
        self,
        goal_id: int,
        step_number: int,
        step_type: str,
        input_data: str,
        reasoning: str,
        conclusion: str,
        confidence_level: float,
    ) -> ReasoningStep:
        """Save a reasoning step."""
        with database_module.SessionLocal() as session:
            step = ReasoningStep(
                goal_id=goal_id,
                step_number=step_number,
                step_type=step_type,
                input_data=input_data,
                reasoning=reasoning,
                conclusion=conclusion,
                confidence_level=confidence_level,
            )
            session.add(step)
            session.commit()
            session.refresh(step)
            return step

    def get_reasoning_steps(self, goal_id: int) -> list[ReasoningStep]:
        """Get all reasoning steps for a goal."""
        with database_module.SessionLocal() as session:
            stmt = (
                select(ReasoningStep)
                .where(ReasoningStep.goal_id == goal_id)
                .order_by(ReasoningStep.step_number)
            )
            return list(session.scalars(stmt).all())

    # Tool Calls
    def save_tool_call(
        self,
        plan_id: int,
        tool_name: str,
        method: str,
        parameters: str,
        **kwargs: Any,
    ) -> ToolCall:
        """Record a tool call."""
        with database_module.SessionLocal() as session:
            call = ToolCall(
                plan_id=plan_id,
                tool_name=tool_name,
                method=method,
                parameters=parameters,
                **{k: v for k, v in kwargs.items() if hasattr(ToolCall, k)},
            )
            session.add(call)
            session.commit()
            session.refresh(call)
            return call

    def get_tool_calls(self, plan_id: int) -> list[ToolCall]:
        """Get all tool calls in a plan."""
        with database_module.SessionLocal() as session:
            stmt = select(ToolCall).where(ToolCall.plan_id == plan_id).order_by(ToolCall.created_at)
            return list(session.scalars(stmt).all())
