from __future__ import annotations

from typing import Any

from acd.infrastructure.repositories.agent.agent_repository import AgentRepository
from acd.infrastructure.agent.ai_orchestrator import AIOrchestrator
from acd.infrastructure.agent.tool_registry import DefaultToolRegistry
from acd.services.ai_execution_service import AIExecutionService


def execute_plan(
    plan_id: int,
    approved: bool = False,
    *,
    repository: AgentRepository | None = None,
    orchestrator: AIOrchestrator | None = None,
    execution_service: AIExecutionService | None = None,
) -> dict[str, Any]:
    """Execute an approved plan.
    
    Args:
        plan_id: ID of plan to execute
        approved: Whether plan is approved by user
        repository: Agent repository
        orchestrator: AI orchestrator
        execution_service: Execution service
        
    Returns:
        Execution results
    """
    if repository is None:
        repository = AgentRepository()
    if orchestrator is None:
        orchestrator = AIOrchestrator(tool_registry=DefaultToolRegistry())
    if execution_service is None:
        execution_service = AIExecutionService(repository)

    # Check plan exists
    plan = repository.get_plan(plan_id)
    if not plan:
        return {"success": False, "error": "Plan not found"}

    # Approve plan if needed
    if approved and not plan.approved_by_user:
        repository.approve_plan(plan_id, approved=True)

    # Check approval
    plan = repository.get_plan(plan_id)
    if not plan.approved_by_user:
        return {
            "success": False,
            "error": "Plan requires approval",
            "plan_id": plan_id,
        }

    # Execute plan
    result = execution_service.execute_plan(plan_id, orchestrator)

    return {
        "success": result.get("success", False),
        "plan_id": plan_id,
        "tasks_executed": result.get("tasks_executed", 0),
        "tasks_failed": result.get("tasks_failed", 0),
        "total_tasks": result.get("tasks_executed", 0) + result.get("tasks_failed", 0),
    }


def approve_plan(
    plan_id: int,
    approved: bool = True,
    *,
    repository: AgentRepository | None = None,
) -> dict[str, Any]:
    """Approve or reject a plan.
    
    Args:
        plan_id: ID of plan to approve
        approved: True to approve, False to reject
        repository: Agent repository
        
    Returns:
        Approval result
    """
    if repository is None:
        repository = AgentRepository()

    plan = repository.approve_plan(plan_id, approved=approved)

    if not plan:
        return {"success": False, "error": "Plan not found"}

    return {
        "success": True,
        "plan_id": plan_id,
        "status": plan.approval_status,
    }


def get_execution_status(
    plan_id: int,
    *,
    execution_service: AIExecutionService | None = None,
) -> dict[str, Any]:
    """Get execution status of a plan.
    
    Args:
        plan_id: ID of plan
        execution_service: Execution service
        
    Returns:
        Execution status
    """
    if execution_service is None:
        execution_service = AIExecutionService()

    return execution_service.get_execution_status(plan_id)
