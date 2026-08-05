from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from acd.application.agent.create_plan import create_plan


def test_create_plan_success():
    """Creates a complete execution plan with tasks."""

    goal = SimpleNamespace(
        id=1,
        title="Goal",
        description="Description",
        objective_type="job_search",
    )

    db_plan = SimpleNamespace(
        id=10,
        title="Execution Plan",
        strategy="Strategy",
    )

    task1 = SimpleNamespace(
        id=100,
        order_index=1,
        task_type="analysis",
        description="Analyze",
        tool_name="tool_a",
    )

    task2 = SimpleNamespace(
        id=101,
        order_index=2,
        task_type="execute",
        description="Execute",
        tool_name="tool_b",
    )

    repository = MagicMock()
    repository.create_goal.return_value = goal
    repository.create_plan.return_value = db_plan
    repository.create_task.side_effect = [task1, task2]
    repository.get_task.side_effect = [task1, task2]

    orchestrator = MagicMock()
    orchestrator.process_goal.return_value = {
        "success": True,
        "requires_approval": True,
        "plan": {
            "title": "Execution Plan",
            "strategy": "Strategy",
            "estimated_duration_hours": 5,
            "tasks": [
                {
                    "type": "analysis",
                    "description": "Analyze",
                    "tool": "tool_a",
                    "order": 1,
                },
                {
                    "type": "execute",
                    "description": "Execute",
                    "tool": "tool_b",
                    "order": 2,
                },
            ],
        },
    }

    memory_service = MagicMock()

    result = create_plan(
        {"title": "Goal"},
        repository=repository,
        orchestrator=orchestrator,
        memory_service=memory_service,
    )

    assert result["success"] is True
    assert result["goal_id"] == 1
    assert result["plan_id"] == 10
    assert result["task_count"] == 2
    assert result["requires_approval"] is True

    repository.create_goal.assert_called_once()
    repository.create_plan.assert_called_once()
    assert repository.create_task.call_count == 2
    memory_service.save_decision.assert_called_once()


# from unittest.mock import patch


def test_create_plan_failure_returns_errors():
    """Returns the orchestrator errors when planning fails."""

    goal = MagicMock()
    goal.id = 1
    goal.title = "Goal"
    goal.description = "Description"
    goal.objective_type = "job_search"

    repository = MagicMock()
    repository.create_goal.return_value = goal

    orchestrator = MagicMock()
    orchestrator.process_goal.return_value = {
        "success": False,
        "errors": ["planning failed"],
    }

    memory_service = MagicMock()

    result = create_plan(
        {"title": "Goal"},
        repository=repository,
        orchestrator=orchestrator,
        memory_service=memory_service,
    )

    assert result == {
        "success": False,
        "errors": ["planning failed"],
    }

    repository.create_plan.assert_not_called()
    repository.create_task.assert_not_called()
    memory_service.save_decision.assert_not_called()


def test_create_plan_creates_default_dependencies():
    """Creates default repository, orchestrator and memory service."""

    repository = MagicMock()

    goal = MagicMock()
    goal.id = 1
    goal.title = "Goal"
    goal.description = ""
    goal.objective_type = "job_search"

    repository.create_goal.return_value = goal

    db_plan = MagicMock()
    db_plan.id = 2
    db_plan.title = "Execution Plan"
    db_plan.strategy = "Strategy"

    repository.create_plan.return_value = db_plan
    repository.get_task.return_value = None

    orchestrator = MagicMock()
    orchestrator.process_goal.return_value = {
        "success": True,
        "plan": {
            "tasks": [],
        },
    }

    memory_service = MagicMock()

    with (
        patch(
            "acd.application.agent.create_plan.AgentRepository",
            return_value=repository,
        ) as repository_cls,
        patch(
            "acd.application.agent.create_plan.DefaultToolRegistry",
            return_value=MagicMock(),
        ),
        patch(
            "acd.application.agent.create_plan.AIOrchestrator",
            return_value=orchestrator,
        ) as orchestrator_cls,
        patch(
            "acd.application.agent.create_plan.AgentMemoryService",
            return_value=memory_service,
        ) as memory_cls,
    ):
        create_plan({})

    repository_cls.assert_called_once_with()
    orchestrator_cls.assert_called_once()
    memory_cls.assert_called_once_with(repository)


def test_create_plan_success_without_tasks():
    """Creates a plan successfully when the orchestrator returns no tasks."""

    from types import SimpleNamespace
    from unittest.mock import MagicMock

    goal = SimpleNamespace(
        id=1,
        title="Goal",
        description="Description",
        objective_type="job_search",
    )

    db_plan = SimpleNamespace(
        id=10,
        title="Execution Plan",
        strategy="Strategy",
    )

    repository = MagicMock()
    repository.create_goal.return_value = goal
    repository.create_plan.return_value = db_plan

    orchestrator = MagicMock()
    orchestrator.process_goal.return_value = {
        "success": True,
        "plan": {
            "title": "Execution Plan",
            "strategy": "Strategy",
            "estimated_duration_hours": 2,
            "tasks": [],
        },
    }

    memory_service = MagicMock()

    result = create_plan(
        {"title": "Goal"},
        repository=repository,
        orchestrator=orchestrator,
        memory_service=memory_service,
    )

    assert result["success"] is True
    assert result["task_count"] == 0
    assert result["tasks"] == []

    repository.create_task.assert_not_called()
    repository.get_task.assert_not_called()

    memory_service.save_decision.assert_called_once()


def test_create_plan_ignores_missing_tasks_from_repository():
    """Skips tasks that cannot be retrieved from the repository."""

    from types import SimpleNamespace
    from unittest.mock import MagicMock

    goal = SimpleNamespace(
        id=1,
        title="Goal",
        description="Description",
        objective_type="job_search",
    )

    db_plan = SimpleNamespace(
        id=10,
        title="Execution Plan",
        strategy="Strategy",
    )

    created_task = SimpleNamespace(id=100)

    repository = MagicMock()
    repository.create_goal.return_value = goal
    repository.create_plan.return_value = db_plan
    repository.create_task.return_value = created_task
    repository.get_task.return_value = None

    orchestrator = MagicMock()
    orchestrator.process_goal.return_value = {
        "success": True,
        "plan": {
            "tasks": [
                {
                    "type": "analysis",
                    "description": "Analyze",
                    "tool": "tool",
                    "order": 1,
                }
            ]
        },
    }

    memory_service = MagicMock()

    result = create_plan(
        {"title": "Goal"},
        repository=repository,
        orchestrator=orchestrator,
        memory_service=memory_service,
    )

    assert result["success"] is True
    assert result["task_count"] == 1
    assert result["tasks"] == []

    repository.get_task.assert_called_once_with(100)




def test_create_plan_uses_default_goal_values():
    """Uses default values when goal_data is empty."""

    goal = SimpleNamespace(
        id=1,
        title="",
        description="",
        objective_type="job_search",
    )

    db_plan = SimpleNamespace(
        id=2,
        title="Execution Plan",
        strategy="",
    )

    repository = MagicMock()
    repository.create_goal.return_value = goal
    repository.create_plan.return_value = db_plan

    orchestrator = MagicMock()
    orchestrator.process_goal.return_value = {
        "success": True,
        "plan": {
            "tasks": [],
        },
    }

    memory_service = MagicMock()

    create_plan(
        {},
        repository=repository,
        orchestrator=orchestrator,
        memory_service=memory_service,
    )

    repository.create_goal.assert_called_once_with(
        title="",
        description="",
        objective_type="job_search",
        priority=1,
    )




def test_create_plan_uses_default_plan_values():
    """Uses default values when optional plan fields are missing."""

    goal = SimpleNamespace(
        id=1,
        title="Goal",
        description="Description",
        objective_type="job_search",
    )

    db_plan = SimpleNamespace(
        id=2,
        title="Execution Plan",
        strategy="",
    )

    repository = MagicMock()
    repository.create_goal.return_value = goal
    repository.create_plan.return_value = db_plan

    orchestrator = MagicMock()
    orchestrator.process_goal.return_value = {
        "success": True,
        "plan": {},
    }

    memory_service = MagicMock()

    result = create_plan(
        {"title": "Goal"},
        repository=repository,
        orchestrator=orchestrator,
        memory_service=memory_service,
    )

    repository.create_plan.assert_called_once_with(
        goal_id=1,
        title="Execution Plan",
        description="",
        strategy="",
        estimated_duration_seconds=3600,
    )

    assert result["estimated_duration_hours"] == 0
    assert result["task_count"] == 0


# from types import SimpleNamespace
# from unittest.mock import MagicMock


def test_create_plan_serializes_task_fields():
    """Serializes task parameters and dependencies before persisting."""

    goal = SimpleNamespace(
        id=1,
        title="Goal",
        description="Description",
        objective_type="job_search",
    )

    db_plan = SimpleNamespace(
        id=2,
        title="Execution Plan",
        strategy="Strategy",
    )

    created_task = SimpleNamespace(id=100)

    repository = MagicMock()
    repository.create_goal.return_value = goal
    repository.create_plan.return_value = db_plan
    repository.create_task.return_value = created_task
    repository.get_task.return_value = SimpleNamespace(
        order_index=1,
        task_type="analysis",
        description="Analyze",
        tool_name="tool",
    )

    orchestrator = MagicMock()
    orchestrator.process_goal.return_value = {
        "success": True,
        "plan": {
            "strategy": "Strategy",
            "estimated_duration_hours": 2.5,
            "tasks": [
                {
                    "type": "analysis",
                    "description": "Analyze",
                    "tool": "tool",
                    "order": 1,
                    "parameters": {"a": 1},
                    "depends_on": [10, 20],
                    "estimated_duration_seconds": 90,
                }
            ],
        },
    }

    memory_service = MagicMock()

    create_plan(
        {"title": "Goal"},
        repository=repository,
        orchestrator=orchestrator,
        memory_service=memory_service,
    )

    kwargs = repository.create_task.call_args.kwargs

    assert kwargs["parameters"] == '{"a": 1}'
    assert kwargs["dependencies"] == "[10, 20]"
    assert kwargs["estimated_duration_seconds"] == 90


# from types import SimpleNamespace
# from unittest.mock import MagicMock


def test_create_plan_converts_hours_to_seconds():
    """Converts estimated_duration_hours to seconds."""

    goal = SimpleNamespace(
        id=1,
        title="Goal",
        description="Description",
        objective_type="job_search",
    )

    db_plan = SimpleNamespace(
        id=2,
        title="Execution Plan",
        strategy="Strategy",
    )

    repository = MagicMock()
    repository.create_goal.return_value = goal
    repository.create_plan.return_value = db_plan

    orchestrator = MagicMock()
    orchestrator.process_goal.return_value = {
        "success": True,
        "plan": {
            "estimated_duration_hours": 1.5,
            "tasks": [],
        },
    }

    memory_service = MagicMock()

    create_plan(
        {"title": "Goal"},
        repository=repository,
        orchestrator=orchestrator,
        memory_service=memory_service,
    )

    assert (
        repository.create_plan.call_args.kwargs[
            "estimated_duration_seconds"
        ]
        == 5400
    )


