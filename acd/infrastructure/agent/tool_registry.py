from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol


class Tool(Protocol):
    """Protocol defining tool interface."""

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute tool with given parameters.

        Returns:
            Dictionary with result data
        """
        ...


class ToolDefinition:
    """Definition of a tool available to the agent."""

    def __init__(
        self,
        name: str,
        category: str,
        description: str,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        execute_func: Callable,
    ) -> None:
        self.name = name
        self.category = category
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.execute_func = execute_func

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for agent context."""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }


class ToolRegistry:
    """Registry of all available tools for the agent."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._tools_by_category: dict[str, list[str]] = {}

    def register(self, tool_def: ToolDefinition) -> None:
        """Register a new tool.

        Args:
            tool_def: Tool definition
        """
        self._tools[tool_def.name] = tool_def

        if tool_def.category not in self._tools_by_category:
            self._tools_by_category[tool_def.category] = []
        self._tools_by_category[tool_def.category].append(tool_def.name)

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get tool by name."""
        return self._tools.get(name)

    def get_tools_by_category(self, category: str) -> list[ToolDefinition]:
        """Get all tools in a category."""
        tool_names = self._tools_by_category.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_all_tools(self) -> list[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())

    def list_categories(self) -> list[str]:
        """List all tool categories."""
        return list(self._tools_by_category.keys())

    def execute_tool(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a tool.

        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
            }

        try:
            result = tool.execute_func(**kwargs)
            return {
                "success": True,
                "tool": tool_name,
                "result": result,
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e),
            }

    def get_available_tools_json(self) -> str:
        """Get all tools as JSON for LLM context."""
        import json

        tools_list = [tool.to_dict() for tool in self.get_all_tools()]
        return json.dumps(tools_list, indent=2, ensure_ascii=False)


class DefaultToolRegistry(ToolRegistry):
    """Default tool registry with built-in tools."""

    def __init__(self) -> None:
        super().__init__()
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register default tools available to agent."""

        # Analysis tools
        self.register(
            ToolDefinition(
                name="analyze_job",
                category="analysis",
                description="Analyze a job posting and match with profile",
                input_schema={"job_id": "string", "profile_id": "string"},
                output_schema={"match_score": "number", "gaps": "array"},
                execute_func=self._analyze_job,
            )
        )

        # Curriculum tools
        self.register(
            ToolDefinition(
                name="generate_curriculum",
                category="curriculum",
                description="Generate curriculum tailored for a job",
                input_schema={"profile_id": "string", "job_id": "string"},
                output_schema={"curriculum_id": "string", "score": "number"},
                execute_func=self._generate_curriculum,
            )
        )

        # Application tools
        self.register(
            ToolDefinition(
                name="submit_application",
                category="application",
                description="Submit job application",
                input_schema={"job_id": "string", "curriculum_id": "string"},
                output_schema={"application_id": "string", "status": "string"},
                execute_func=self._submit_application,
            )
        )

        # Workflow tools
        self.register(
            ToolDefinition(
                name="execute_workflow",
                category="workflow",
                description="Execute workflow to automate tasks",
                input_schema={"workflow_type": "string", "parameters": "object"},
                output_schema={"execution_id": "string", "status": "string"},
                execute_func=self._execute_workflow,
            )
        )

        # Career tools
        self.register(
            ToolDefinition(
                name="assess_career_gap",
                category="career",
                description="Assess gaps between current profile and goal",
                input_schema={"profile_id": "string", "goal_id": "string"},
                output_schema={"compatibility": "number", "gaps": "array"},
                execute_func=self._assess_career_gap,
            )
        )

        # Analytics tools
        self.register(
            ToolDefinition(
                name="get_analytics",
                category="analytics",
                description="Get analytics and metrics",
                input_schema={"metric_type": "string"},
                output_schema={"data": "object", "timestamp": "string"},
                execute_func=self._get_analytics,
            )
        )

    # Default tool implementations (stubs for now)
    @staticmethod
    def _analyze_job(**kwargs: Any) -> dict[str, Any]:
        return {"match_score": 0.75, "gaps": []}

    @staticmethod
    def _generate_curriculum(**kwargs: Any) -> dict[str, Any]:
        return {"curriculum_id": "cv_001", "score": 0.85}

    @staticmethod
    def _submit_application(**kwargs: Any) -> dict[str, Any]:
        return {"application_id": "app_001", "status": "submitted"}

    @staticmethod
    def _execute_workflow(**kwargs: Any) -> dict[str, Any]:
        return {"execution_id": "exec_001", "status": "completed"}

    @staticmethod
    def _assess_career_gap(**kwargs: Any) -> dict[str, Any]:
        return {"compatibility": 0.65, "gaps": ["skill1", "skill2"]}

    @staticmethod
    def _get_analytics(**kwargs: Any) -> dict[str, Any]:
        return {"data": {}, "timestamp": "2026-07-01T00:00:00Z"}
