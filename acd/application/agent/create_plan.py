from __future__ import annotations

import json
from typing import Any

from acd.infrastructure.agent.ai_orchestrator import AIOrchestrator
from acd.infrastructure.agent.tool_registry import DefaultToolRegistry
from acd.infrastructure.repositories.agent.agent_repository import AgentRepository
from acd.services.ai_execution_service import AgentMemoryService


def create_plan(
    goal_data: dict[str, Any],
    *,
    repository: AgentRepository | None = None,
    orchestrator: AIOrchestrator | None = None,
    memory_service: AgentMemoryService | None = None,
) -> dict[str, Any]:
    """Create an execution plan for a goal.

    Args:
        goal_data: Goal details (title, description, objective_type, priority)
        repository: Agent repository
        orchestrator: AI orchestrator
        memory_service: Memory service

    Returns:
        Execution plan with tasks and approval status
    """
    if repository is None:
        repository = AgentRepository()
    if orchestrator is None:
        orchestrator = AIOrchestrator(tool_registry=DefaultToolRegistry())
    if memory_service is None:
        memory_service = AgentMemoryService(repository)

    # Create goal in database
    goal = repository.create_goal(
        title=goal_data.get("title", ""),
        description=goal_data.get("description", ""),
        objective_type=goal_data.get("objective_type", "job_search"),
        priority=goal_data.get("priority", 1),
    )

    # Process goal through orchestrator
    plan_result = orchestrator.process_goal(
        {
            "id": goal.id,
            "title": goal.title,
            "description": goal.description,
            "objective_type": goal.objective_type,
        }
    )

    if not plan_result.get("success"):
        return {
            "success": False,
            "errors": plan_result.get("errors", []),
        }

    plan_data = plan_result.get("plan", {})

    # Create plan in database
    db_plan = repository.create_plan(
        goal_id=goal.id,
        title=plan_data.get("title", "Execution Plan"),
        description=plan_data.get("strategy", ""),
        strategy=plan_data.get("strategy", ""),
        estimated_duration_seconds=int(plan_data.get("estimated_duration_hours", 1) * 3600),
    )

    # Create tasks in database
    task_ids = []
    for task in plan_data.get("tasks", []):
        db_task = repository.create_task(
            plan_id=db_plan.id,
            task_type=task.get("type", ""),
            description=task.get("description", ""),
            tool_name=task.get("tool", ""),
            order_index=task.get("order", 0),
            parameters=json.dumps(task.get("parameters", {})),
            dependencies=json.dumps(task.get("depends_on", [])),
            estimated_duration_seconds=task.get("estimated_duration_seconds", 0),
        )
        task_ids.append(db_task.id)

    # Save plan decision to memory
    memory_service.save_decision(
        goal.id,
        f"Created plan with {len(task_ids)} tasks",
        plan_data.get("strategy", ""),
    )

    return {
        "success": True,
        "goal_id": goal.id,
        "plan_id": db_plan.id,
        "title": db_plan.title,
        "strategy": db_plan.strategy,
        "task_count": len(task_ids),
        "requires_approval": plan_result.get("requires_approval", False),
        "estimated_duration_hours": plan_data.get("estimated_duration_hours", 0),
        "tasks": [
            {
                "order": t.order_index,
                "type": t.task_type,
                "description": t.description,
                "tool": t.tool_name,
            }
            for t in [repository.get_task(tid) for tid in task_ids]
            if t
        ],
    }
