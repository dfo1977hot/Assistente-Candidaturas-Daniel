from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from acd.infrastructure.agent.context_builder import ContextBuilder
from acd.infrastructure.agent.planning_engine import PlanningEngine
from acd.infrastructure.agent.tool_registry import DefaultToolRegistry, ToolRegistry


class AIOrchestrator:
    """Main orchestrator coordinating all agent activities.

    Responsibilities:
    - Understand objectives
    - Decompose problems
    - Create plans
    - Select tools
    - Execute tasks
    - Monitor execution
    """

    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        planning_engine: PlanningEngine | None = None,
    ) -> None:
        self.tool_registry = tool_registry or DefaultToolRegistry()
        self.planning_engine = planning_engine or PlanningEngine()
        self.context_builder = ContextBuilder()
        self._execution_history: list[dict[str, Any]] = []
        self._current_plan: dict[str, Any] | None = None

    def process_goal(self, goal: dict[str, Any]) -> dict[str, Any]:
        """Process a goal and create an execution plan.

        Args:
            goal: Goal object with title, description, objective_type

        Returns:
            Dictionary with plan details, strategy, tasks, approval status
        """
        # Build context
        context = self.context_builder.build()

        # Create plan
        plan = self.planning_engine.create_plan(goal, context)

        # Validate plan
        is_valid, errors = self.planning_engine.validate_plan(plan)

        if not is_valid:
            return {
                "success": False,
                "errors": errors,
                "plan": None,
            }

        # Determine if approval is needed
        plan["requires_human_approval"] = plan.get("requires_human_approval", False) or any(
            task.get("requires_approval", False) for task in plan.get("tasks", [])
        )

        # Store plan
        self._current_plan = plan

        return {
            "success": True,
            "plan": plan,
            "requires_approval": plan.get("requires_human_approval", False),
            "strategy": plan.get("strategy", ""),
            "estimated_duration_hours": plan.get("estimated_duration_hours", 0),
            "task_count": len(plan.get("tasks", [])),
        }

    def analyze_request(self, user_request: str) -> dict[str, Any]:
        """Analyze a natural language request and determine action.

        Args:
            user_request: Natural language user request

        Returns:
            Analysis with intent, recommended goal type, and next steps
        """
        # Intent classification (simplified - in real scenario would use LLM)
        intent_keywords = {
            "job_search": ["vaga", "aplicar", "candidatar", "job", "apply", "position"],
            "career_planning": [
                "carreira",
                "planejamento",
                "desenvolvimento",
                "career",
                "planning",
            ],
            "skill": ["habilidade", "skill", "aprender", "aprimorar", "improve", "learn"],
            "interview": ["entrevista", "interview", "preparar", "prepare"],
            "analysis": ["analisar", "analyze", "como", "qual", "what", "which"],
        }

        request_lower = user_request.lower()
        detected_intents = []

        for intent, keywords in intent_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                detected_intents.append(intent)

        primary_intent = detected_intents[0] if detected_intents else "job_search"

        return {
            "intent": primary_intent,
            "confidence": 0.8 if detected_intents else 0.5,
            "request": user_request,
            "requires_clarification": len(detected_intents) > 1,
            "next_action": f"create_goal_{primary_intent}",
        }

    def decompose_problem(self, goal: dict[str, Any]) -> dict[str, Any]:
        """Decompose a complex problem into manageable tasks.

        Args:
            goal: Goal to decompose

        Returns:
            Decomposed tasks with dependencies
        """
        context = self.context_builder.build()
        plan = self.planning_engine.create_plan(goal, context)

        # Decompose each task further if needed
        detailed_tasks = []
        for task in plan.get("tasks", []):
            subtasks = self.planning_engine.decompose_task(task, context)
            task["subtasks"] = subtasks
            detailed_tasks.append(task)

        return {
            "goal_id": goal.get("id"),
            "strategy": plan.get("strategy", ""),
            "tasks": detailed_tasks,
            "total_subtasks": sum(len(t.get("subtasks", [])) for t in detailed_tasks),
        }

    def select_tools(self, task: dict[str, Any]) -> list[str]:
        """Select appropriate tools for a task.

        Args:
            task: Task requiring tools

        Returns:
            List of recommended tool names
        """
        task_type = task.get("type", "")
        tool_category = task.get("tool", "")

        if tool_category:
            tools = self.tool_registry.get_tools_by_category(tool_category)
            return [t.name for t in tools]

        # Fallback based on task type
        type_to_tools = {
            "analyze": ["analyze_job"],
            "search": ["execute_workflow"],
            "generate_cv": ["generate_curriculum"],
            "apply": ["submit_application"],
            "assess": ["assess_career_gap"],
        }

        return type_to_tools.get(task_type, [])

    def approve_plan(self, plan_id: str | None = None, approved: bool = True) -> dict[str, Any]:
        """Approve or reject a plan.

        Args:
            plan_id: Plan ID (if None, uses current plan)
            approved: Whether plan is approved

        Returns:
            Approval status
        """
        plan = self._current_plan
        if not plan:
            return {"success": False, "error": "No plan to approve"}

        plan["approval_status"] = "approved" if approved else "rejected"
        plan["approved_at"] = datetime.now(UTC).isoformat()
        plan["approved_by_user"] = approved

        return {
            "success": True,
            "plan_id": plan.get("id"),
            "status": plan["approval_status"],
            "timestamp": plan["approved_at"],
        }

    def execute_plan(self, plan_id: str | None = None) -> dict[str, Any]:
        """Execute an approved plan.

        Args:
            plan_id: Plan ID to execute

        Returns:
            Execution status and results
        """
        plan = self._current_plan
        if not plan:
            return {"success": False, "error": "No plan to execute"}

        if not plan.get("approved_by_user"):
            return {"success": False, "error": "Plan not approved by user"}

        execution_result = {
            "plan_id": plan.get("id"),
            "start_time": datetime.now(UTC).isoformat(),
            "tasks_executed": 0,
            "tasks_failed": 0,
            "results": [],
        }

        # Execute tasks in order
        for task in plan.get("tasks", []):
            task_result = self._execute_task(task)
            execution_result["results"].append(task_result)

            if task_result.get("success"):
                execution_result["tasks_executed"] += 1
            else:
                execution_result["tasks_failed"] += 1

        execution_result["end_time"] = datetime.now(UTC).isoformat()
        execution_result["success"] = execution_result["tasks_failed"] == 0

        # Record in history
        self._execution_history.append(execution_result)

        return execution_result

    def _execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a single task using appropriate tool.

        Args:
            task: Task to execute

        Returns:
            Task execution result
        """
        tool_name = task.get("tool", "")
        if not tool_name:
            return {
                "task_id": task.get("order"),
                "success": False,
                "error": "No tool specified for task",
            }

        # Execute tool
        result = self.tool_registry.execute_tool(tool_name, **task.get("parameters", {}))

        return {
            "task_id": task.get("order"),
            "tool": tool_name,
            "success": result.get("success", False),
            "result": result.get("result"),
            "error": result.get("error"),
        }

    def get_execution_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get execution history.

        Args:
            limit: Number of recent executions to return

        Returns:
            List of recent executions
        """
        return self._execution_history[-limit:]

    def get_agent_status(self) -> dict[str, Any]:
        """Get current agent status.

        Returns:
            Agent status and statistics
        """
        history = self._execution_history

        return {
            "current_plan_id": self._current_plan.get("id") if self._current_plan else None,
            "total_executions": len(history),
            "successful_executions": len([h for h in history if h.get("success", False)]),
            "failed_executions": len([h for h in history if not h.get("success", False)]),
            "success_rate": (
                len([h for h in history if h.get("success")]) / len(history) if history else 0
            ),
            "available_tools": len(self.tool_registry.get_all_tools()),
            "tool_categories": self.tool_registry.list_categories(),
        }

    def reset_plan(self) -> dict[str, Any]:
        """Reset current plan."""
        self._current_plan = None
        return {"success": True, "message": "Plan reset"}
