from __future__ import annotations

from typing import Any
import json
from datetime import datetime

from acd.infrastructure.repositories.agent.agent_repository import AgentRepository
from acd.infrastructure.agent.ai_orchestrator import AIOrchestrator
from acd.infrastructure.agent.tool_registry import ToolRegistry


class AIExecutionService:
    """Service for executing agent plans."""

    def __init__(self, repository: AgentRepository | None = None) -> None:
        self.repository = repository or AgentRepository()

    def execute_plan(
        self,
        plan_id: int,
        orchestrator: AIOrchestrator,
    ) -> dict[str, Any]:
        """Execute a plan.
        
        Args:
            plan_id: ID of plan to execute
            orchestrator: AI Orchestrator instance
            
        Returns:
            Execution result
        """
        plan = self.repository.get_plan(plan_id)
        if not plan:
            return {"success": False, "error": "Plan not found"}

        if not plan.approved_by_user:
            return {"success": False, "error": "Plan not approved"}

        # Update plan status
        self.repository.update_plan(plan_id, status="executing", started_at=datetime.utcnow())

        # Execute tasks
        tasks = self.repository.list_tasks_by_plan(plan_id)
        results = []
        completed = 0

        for task in tasks:
            try:
                result = self._execute_task(task, orchestrator)
                results.append(result)

                # Update task
                self.repository.update_task(
                    task.id,
                    status="completed" if result.get("success") else "failed",
                    result=json.dumps(result.get("result", {})),
                    error_message=result.get("error"),
                )

                if result.get("success"):
                    completed += 1

            except Exception as e:
                self.repository.update_task(
                    task.id,
                    status="failed",
                    error_message=str(e),
                )

        # Update plan with results
        progress = (completed / len(tasks) * 100) if tasks else 0
        self.repository.update_plan(
            plan_id,
            status="completed",
            progress_percentage=int(progress),
            completed_at=datetime.utcnow(),
            result_summary=json.dumps({"total": len(tasks), "completed": completed, "failed": len(tasks) - completed}),
        )

        return {
            "success": completed == len(tasks),
            "plan_id": plan_id,
            "tasks_executed": completed,
            "tasks_failed": len(tasks) - completed,
            "results": results,
        }

    def _execute_task(self, task, orchestrator: AIOrchestrator) -> dict[str, Any]:
        """Execute a single task."""
        tool = orchestrator.tool_registry.get_tool(task.tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{task.tool_name}' not available",
            }

        # Parse parameters
        params = {}
        if task.parameters:
            try:
                params = json.loads(task.parameters)
            except json.JSONDecodeError:
                params = {}

        # Execute tool
        result = orchestrator.tool_registry.execute_tool(task.tool_name, **params)

        return result

    def get_execution_status(self, plan_id: int) -> dict[str, Any]:
        """Get execution status of a plan."""
        plan = self.repository.get_plan(plan_id)
        if not plan:
            return {"success": False, "error": "Plan not found"}

        tasks = self.repository.list_tasks_by_plan(plan_id)
        completed_tasks = [t for t in tasks if t.status == "completed"]
        failed_tasks = [t for t in tasks if t.status == "failed"]

        return {
            "plan_id": plan_id,
            "status": plan.status,
            "progress_percentage": plan.progress_percentage,
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "pending_tasks": len(tasks) - len(completed_tasks) - len(failed_tasks),
            "started_at": plan.started_at.isoformat() if plan.started_at else None,
            "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
        }

    def cancel_plan(self, plan_id: int) -> dict[str, Any]:
        """Cancel a plan execution."""
        plan = self.repository.get_plan(plan_id)
        if not plan:
            return {"success": False, "error": "Plan not found"}

        if plan.status not in ["pending", "executing"]:
            return {"success": False, "error": f"Cannot cancel plan in '{plan.status}' status"}

        self.repository.update_plan(
            plan_id,
            status="cancelled",
            completed_at=datetime.utcnow(),
        )

        return {"success": True, "plan_id": plan_id}


class AgentMemoryService:
    """Service for managing agent memory."""

    def __init__(self, repository: AgentRepository | None = None) -> None:
        self.repository = repository or AgentRepository()

    def save_decision(self, goal_id: int, decision: str, reasoning: str) -> dict[str, Any]:
        """Save a decision to memory."""
        memory = self.repository.save_memory(
            memory_type="decision",
            key=f"decision_{goal_id}_{datetime.utcnow().timestamp()}",
            value=json.dumps({"decision": decision, "reasoning": reasoning}),
            importance=7,
        )

        return {"success": True, "memory_id": memory.id}

    def save_preference(self, key: str, value: Any) -> dict[str, Any]:
        """Save user preference."""
        memory = self.repository.save_memory(
            memory_type="preference",
            key=key,
            value=json.dumps(value),
            importance=8,
        )

        return {"success": True, "memory_id": memory.id}

    def get_recent_decisions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent decisions."""
        memories = self.repository.list_memory_by_type("decision", limit=limit)
        return [
            {
                "key": m.key,
                "value": json.loads(m.value) if m.value else {},
                "created_at": m.created_at.isoformat(),
            }
            for m in memories
        ]

    def get_user_preferences(self) -> dict[str, Any]:
        """Get all user preferences from memory."""
        memories = self.repository.list_memory_by_type("preference", limit=100)
        preferences = {}

        for m in memories:
            try:
                preferences[m.key] = json.loads(m.value)
            except json.JSONDecodeError:
                preferences[m.key] = m.value

        return preferences

    def get_conversation_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get conversation history."""
        memories = self.repository.list_memory_by_type("conversation", limit=limit)
        return [
            {
                "message": json.loads(m.value) if m.value else {},
                "created_at": m.created_at.isoformat(),
            }
            for m in memories
        ]

    def save_conversation(self, user_message: str, agent_response: str) -> dict[str, Any]:
        """Save conversation turn."""
        memory = self.repository.save_memory(
            memory_type="conversation",
            key=f"conv_{datetime.utcnow().timestamp()}",
            value=json.dumps({"user": user_message, "agent": agent_response}),
            importance=5,
        )

        return {"success": True, "memory_id": memory.id}
