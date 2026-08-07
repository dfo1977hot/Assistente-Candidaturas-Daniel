from __future__ import annotations

from typing import Any


class PlanningEngine:
    """Transforms goals into executable tasks and strategies."""

    def __init__(self) -> None:
        self.strategies = {
            "job_search": self._plan_job_search,
            "career_planning": self._plan_career_development,
            "skill_improvement": self._plan_skill_improvement,
            "interview_prep": self._plan_interview_prep,
        }

    def create_plan(self, goal: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Create execution plan for a goal.

        Args:
            goal: Goal object with title, description, objective_type
            context: Context from ContextBuilder

        Returns:
            Plan with strategy, tasks, dependencies, and timeline
        """
        goal_type = goal.get("objective_type", "job_search")
        strategy_func = self.strategies.get(goal_type, self._plan_job_search)

        plan = strategy_func(goal, context)
        plan["goal_id"] = goal.get("id")
        plan["title"] = goal.get("title", "Execution Plan")

        return plan

    def _plan_job_search(self, goal: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Plan for job search goal."""
        tasks = [
            {
                "type": "analyze",
                "description": "Analyze profile and identify job market match",
                "tool": "analysis",
                "order": 1,
                "depends_on": [],
            },
            {
                "type": "search",
                "description": "Search for matching job opportunities",
                "tool": "job_search",
                "order": 2,
                "depends_on": [1],
            },
            {
                "type": "filter",
                "description": "Filter jobs by match score and criteria",
                "tool": "analysis",
                "order": 3,
                "depends_on": [2],
            },
            {
                "type": "generate_cv",
                "description": "Generate tailored curriculum for best matches",
                "tool": "curriculum",
                "order": 4,
                "depends_on": [3],
            },
            {
                "type": "apply",
                "description": "Submit applications to qualified positions",
                "tool": "application",
                "order": 5,
                "depends_on": [4],
                "requires_approval": True,
            },
            {
                "type": "track",
                "description": "Register applications in CRM and track progress",
                "tool": "workflow",
                "order": 6,
                "depends_on": [5],
            },
        ]

        return {
            "strategy": "Systematic job search with tailored applications",
            "tasks": tasks,
            "estimated_duration_hours": 8,
            "requires_human_approval": False,
        }

    def _plan_career_development(
        self, goal: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Plan for career development goal."""
        tasks = [
            {
                "type": "assess",
                "description": "Assess current skills and career gap",
                "tool": "career",
                "order": 1,
                "depends_on": [],
            },
            {
                "type": "plan",
                "description": "Create development plan with milestones",
                "tool": "career",
                "order": 2,
                "depends_on": [1],
            },
            {
                "type": "recommend",
                "description": "Get targeted skill improvement recommendations",
                "tool": "career",
                "order": 3,
                "depends_on": [2],
            },
            {
                "type": "track",
                "description": "Set up tracking and monitoring",
                "tool": "workflow",
                "order": 4,
                "depends_on": [3],
            },
        ]

        return {
            "strategy": "Structured career development with measurable progress",
            "tasks": tasks,
            "estimated_duration_hours": 4,
            "requires_human_approval": False,
        }

    def _plan_skill_improvement(
        self, goal: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Plan for skill improvement goal."""
        tasks = [
            {
                "type": "identify",
                "description": "Identify specific skill gaps",
                "tool": "career",
                "order": 1,
                "depends_on": [],
            },
            {
                "type": "research",
                "description": "Research learning resources and paths",
                "tool": "knowledge",
                "order": 2,
                "depends_on": [1],
            },
            {
                "type": "create_plan",
                "description": "Create learning schedule",
                "tool": "workflow",
                "order": 3,
                "depends_on": [2],
            },
        ]

        return {
            "strategy": "Targeted skill development with practical learning paths",
            "tasks": tasks,
            "estimated_duration_hours": 2,
            "requires_human_approval": False,
        }

    def _plan_interview_prep(self, goal: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Plan for interview preparation."""
        tasks = [
            {
                "type": "analyze_company",
                "description": "Research company and role",
                "tool": "analysis",
                "order": 1,
                "depends_on": [],
            },
            {
                "type": "identify_gaps",
                "description": "Identify potential questions and gaps",
                "tool": "career",
                "order": 2,
                "depends_on": [1],
            },
            {
                "type": "prepare_answers",
                "description": "Generate potential answers using AI",
                "tool": "ai",
                "order": 3,
                "depends_on": [2],
            },
            {
                "type": "simulate",
                "description": "Simulate interview scenarios",
                "tool": "workflow",
                "order": 4,
                "depends_on": [3],
            },
        ]

        return {
            "strategy": "Comprehensive interview preparation with simulations",
            "tasks": tasks,
            "estimated_duration_hours": 6,
            "requires_human_approval": False,
        }

    def decompose_task(self, task: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        """Decompose a complex task into subtasks.

        Args:
            task: Task to decompose
            context: Execution context

        Returns:
            List of subtasks
        """
        task_type = task.get("type", "generic")

        if task_type == "search":
            return self._decompose_search(task, context)
        elif task_type == "apply":
            return self._decompose_apply(task, context)
        elif task_type == "analyze":
            return self._decompose_analyze(task, context)

        return [task]

    def _decompose_search(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Decompose job search task."""
        return [
            {"type": "search_by_role", "description": "Search by target roles"},
            {"type": "search_by_location", "description": "Search by location"},
            {"type": "search_by_company", "description": "Search at target companies"},
            {"type": "consolidate", "description": "Consolidate and deduplicate results"},
        ]

    def _decompose_apply(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Decompose application task."""
        return [
            {"type": "select_cv", "description": "Select appropriate curriculum"},
            {"type": "generate_letter", "description": "Generate cover letter if needed"},
            {"type": "fill_form", "description": "Fill application form"},
            {"type": "submit", "description": "Submit application"},
            {"type": "register_crm", "description": "Register in CRM"},
        ]

    def _decompose_analyze(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Decompose analysis task."""
        return [
            {"type": "load_profile", "description": "Load user profile"},
            {"type": "calculate_ats", "description": "Calculate ATS score"},
            {"type": "identify_gaps", "description": "Identify skill gaps"},
            {"type": "generate_report", "description": "Generate analysis report"},
        ]

    def validate_plan(self, plan: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate if plan is executable.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        tasks = plan.get("tasks", [])
        if not tasks:
            errors.append("Plan has no tasks")

        # Check dependencies
        task_ids = {t.get("order"): t for t in tasks}
        for task in tasks:
            depends_on = task.get("depends_on", [])
            for dep_id in depends_on:
                if dep_id not in task_ids:
                    errors.append(f"Task {task.get('order')} depends on non-existent task {dep_id}")

        # Check for circular dependencies
        if self._has_circular_dependency(tasks):
            errors.append("Plan has circular task dependencies")

        return len(errors) == 0, errors

    def _has_circular_dependency(self, tasks: list[dict[str, Any]]) -> bool:
        """Check if task dependencies have cycles."""
        # Simple cycle detection
        visited = set()
        rec_stack = set()

        def has_cycle(task_id, graph):
            visited.add(task_id)
            rec_stack.add(task_id)

            for neighbor in graph.get(task_id, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, graph):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(task_id)
            return False

        # Build adjacency list
        graph = {}
        for task in tasks:
            task_id = task.get("order")
            graph[task_id] = task.get("depends_on", [])

        for task_id in graph:
            if task_id not in visited:
                if has_cycle(task_id, graph):
                    return True

        return False
