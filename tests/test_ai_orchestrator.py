import os
import tempfile

import pytest

from acd.application.agent.ask_agent import ask_agent
from acd.application.agent.create_plan import create_plan
from acd.application.agent.execute_plan import approve_plan, execute_plan
from acd.database import database as database_module
from acd.infrastructure.agent.ai_orchestrator import AIOrchestrator
from acd.infrastructure.agent.context_builder import ContextBuilder
from acd.infrastructure.agent.planning_engine import PlanningEngine
from acd.infrastructure.agent.tool_registry import DefaultToolRegistry, ToolDefinition, ToolRegistry
from acd.infrastructure.repositories.agent.agent_repository import AgentRepository
from acd.services.ai_execution_service import AgentMemoryService, AIExecutionService


@pytest.fixture
def temp_database(monkeypatch):
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp(prefix="acd-agent-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd_agent.db")
    monkeypatch.setattr("acd.database.database.DATABASE_URL", f"sqlite:///{db_path}")

    # Import all entities FIRST to register ORM metadata

    database_module.engine.dispose()
    database_module.engine = database_module.create_engine(
        f"sqlite:///{db_path}", echo=False, future=True
    )
    database_module.SessionLocal = database_module.sessionmaker(
        bind=database_module.engine, autoflush=False, autocommit=False
    )

    from acd.models.base import Base

    Base.metadata.create_all(database_module.engine)

    yield

    Base.metadata.drop_all(database_module.engine)


class TestToolRegistry:
    """Test tool registry functionality."""

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()

        tool_def = ToolDefinition(
            name="test_tool",
            category="test",
            description="Test tool",
            input_schema={"param": "string"},
            output_schema={"result": "string"},
            execute_func=lambda **kwargs: {"result": "ok"},
        )

        registry.register(tool_def)

        assert registry.get_tool("test_tool") is not None
        assert registry.get_tool("test_tool").name == "test_tool"

    def test_get_tools_by_category(self):
        """Test retrieving tools by category."""
        registry = DefaultToolRegistry()

        analysis_tools = registry.get_tools_by_category("analysis")
        assert len(analysis_tools) > 0
        assert all(t.category == "analysis" for t in analysis_tools)

    def test_execute_tool(self):
        """Test tool execution."""
        registry = DefaultToolRegistry()

        result = registry.execute_tool("analyze_job", job_id="123", profile_id="456")

        assert result.get("success") is True
        assert "result" in result


class TestContextBuilder:
    """Test context builder."""

    def test_build_context(self):
        """Test building context."""
        builder = ContextBuilder()

        builder.add_user_profile(
            {
                "skills": ["Python", "SQL"],
                "experience_years": 5,
            }
        ).add_career_goals(
            [
                {"title": "Senior Developer"},
            ]
        )

        context = builder.build()

        assert "user_profile" in context
        assert "career_goals" in context
        assert len(context["user_profile"]["skills"]) == 2

    def test_context_summary(self):
        """Test getting context summary."""
        builder = ContextBuilder()

        builder.add_user_profile(
            {
                "skills": ["Python"],
                "experience_years": 3,
            }
        )

        summary = builder.get_context_summary()

        assert "Python" in summary
        assert "3" in summary

    def test_available_tools_context(self):
        """Test getting tools context."""
        builder = ContextBuilder()
        registry = DefaultToolRegistry()

        tools_context = builder.get_available_tools_context(registry)

        assert "analyze_job" in tools_context
        assert "Available Tools" in tools_context


class TestPlanningEngine:
    """Test planning engine."""

    def test_create_job_search_plan(self):
        """Test creating job search plan."""
        engine = PlanningEngine()

        goal = {
            "id": 1,
            "title": "Find job",
            "objective_type": "job_search",
        }

        plan = engine.create_plan(goal, {})

        assert plan.get("strategy") is not None
        assert len(plan.get("tasks", [])) > 0
        assert len(plan.get("tasks", [])) == 6  # job_search should have 6 tasks

    def test_create_career_development_plan(self):
        """Test creating career development plan."""
        engine = PlanningEngine()

        goal = {
            "id": 1,
            "title": "Career development",
            "objective_type": "career_planning",
        }

        plan = engine.create_plan(goal, {})

        assert plan.get("strategy") is not None
        assert len(plan.get("tasks", [])) > 0

    def test_validate_plan(self):
        """Test plan validation."""
        engine = PlanningEngine()

        plan = {
            "tasks": [
                {"order": 1, "type": "analyze", "depends_on": []},
                {"order": 2, "type": "plan", "depends_on": [1]},
            ]
        }

        is_valid, errors = engine.validate_plan(plan)

        assert is_valid is True
        assert len(errors) == 0

    def test_decompose_task(self):
        """Test task decomposition."""
        engine = PlanningEngine()

        task = {"type": "search"}
        subtasks = engine.decompose_task(task, {})

        assert len(subtasks) > 0


class TestAIOrchestrator:
    """Test AI orchestrator."""

    def test_analyze_request(self):
        """Test request analysis."""
        orchestrator = AIOrchestrator()

        result = orchestrator.analyze_request("Quero conseguir uma vaga de desenvolvedor")

        assert "intent" in result
        assert "confidence" in result

    def test_process_goal(self):
        """Test goal processing."""
        orchestrator = AIOrchestrator()

        goal = {
            "id": 1,
            "title": "Find job",
            "description": "Find a job as developer",
            "objective_type": "job_search",
        }

        result = orchestrator.process_goal(goal)

        assert result.get("success") is True
        assert "plan" in result

    def test_get_agent_status(self):
        """Test getting agent status."""
        orchestrator = AIOrchestrator()

        status = orchestrator.get_agent_status()

        assert "total_executions" in status
        assert "available_tools" in status


class TestAgentRepository:
    """Test agent repository."""

    def test_create_goal(self, temp_database):
        """Test creating a goal."""
        repo = AgentRepository()

        goal = repo.create_goal(
            title="Test Goal",
            description="Test Description",
            objective_type="job_search",
        )

        assert goal.id is not None
        assert goal.title == "Test Goal"

    def test_create_and_list_goals(self, temp_database):
        """Test creating and listing goals."""
        repo = AgentRepository()

        repo.create_goal("Goal 1", "Desc 1", "job_search")
        repo.create_goal("Goal 2", "Desc 2", "career_planning")

        goals = repo.list_goals()

        assert len(goals) >= 2

    def test_create_plan(self, temp_database):
        """Test creating a plan."""
        repo = AgentRepository()

        goal = repo.create_goal("Test", "Test", "job_search")
        plan = repo.create_plan(
            goal_id=goal.id,
            title="Test Plan",
            description="Test",
            strategy="Test Strategy",
            estimated_duration_seconds=3600,
        )

        assert plan.id is not None
        assert plan.goal_id == goal.id

    def test_create_task(self, temp_database):
        """Test creating a task."""
        repo = AgentRepository()

        goal = repo.create_goal("Test", "Test", "job_search")
        plan = repo.create_plan(goal.id, "Plan", "Desc", "Strategy", 3600)
        task = repo.create_task(
            plan_id=plan.id,
            task_type="analyze",
            description="Test task",
            tool_name="analysis",
            order_index=1,
        )

        assert task.id is not None
        assert task.plan_id == plan.id


class TestAIExecutionService:
    """Test execution service."""

    def test_get_execution_status(self, temp_database):
        """Test getting execution status."""
        repo = AgentRepository()
        service = AIExecutionService(repo)

        goal = repo.create_goal("Test", "Test", "job_search")
        plan = repo.create_plan(goal.id, "Plan", "Desc", "Strategy", 3600)

        status = service.get_execution_status(plan.id)

        assert status.get("plan_id") == plan.id
        assert "progress_percentage" in status

    def test_cancel_plan(self, temp_database):
        """Test canceling a plan."""
        repo = AgentRepository()
        service = AIExecutionService(repo)

        goal = repo.create_goal("Test", "Test", "job_search")
        plan = repo.create_plan(goal.id, "Plan", "Desc", "Strategy", 3600)

        result = service.cancel_plan(plan.id)

        assert result.get("success") is True


class TestAgentMemoryService:
    """Test memory service."""

    def test_save_decision(self, temp_database):
        """Test saving decision."""
        repo = AgentRepository()
        service = AgentMemoryService(repo)

        result = service.save_decision(1, "Apply to job", "Good match")

        assert result.get("success") is True
        assert "memory_id" in result

    def test_save_preference(self, temp_database):
        """Test saving preference."""
        repo = AgentRepository()
        service = AgentMemoryService(repo)

        result = service.save_preference("salary_min", 5000)

        assert result.get("success") is True

    def test_get_recent_decisions(self, temp_database):
        """Test getting recent decisions."""
        repo = AgentRepository()
        service = AgentMemoryService(repo)

        service.save_decision(1, "Decision 1", "Reasoning 1")
        service.save_decision(1, "Decision 2", "Reasoning 2")

        decisions = service.get_recent_decisions(limit=10)

        assert len(decisions) >= 2


class TestApplicationLayer:
    """Test application layer use cases."""

    def test_ask_agent(self, temp_database):
        """Test asking agent."""
        result = ask_agent("Quero conseguir uma vaga de desenvolvedor Python")

        assert result.get("success") is True
        assert "intent" in result

    def test_create_plan_use_case(self, temp_database):
        """Test create plan use case."""
        goal_data = {
            "title": "Find job",
            "description": "Find a Python developer position",
            "objective_type": "job_search",
            "priority": 1,
        }

        result = create_plan(goal_data)

        assert result.get("success") is True
        assert "plan_id" in result
        assert "task_count" in result

    def test_approve_plan_use_case(self, temp_database):
        """Test approve plan use case."""
        # First create a plan
        goal_data = {
            "title": "Test",
            "description": "Test",
            "objective_type": "job_search",
        }

        plan_result = create_plan(goal_data)
        plan_id = plan_result["plan_id"]

        # Then approve it
        result = approve_plan(plan_id, approved=True)

        assert result.get("success") is True
        assert result.get("status") == "approved"

    def test_execute_plan_use_case(self, temp_database):
        """Test execute plan use case."""
        # Create and approve plan
        goal_data = {
            "title": "Test",
            "description": "Test",
            "objective_type": "job_search",
        }

        plan_result = create_plan(goal_data)
        plan_id = plan_result["plan_id"]

        # Approve
        approve_plan(plan_id, approved=True)

        # Execute
        result = execute_plan(plan_id, approved=True)

        assert "plan_id" in result
