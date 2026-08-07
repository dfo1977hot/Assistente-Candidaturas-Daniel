from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from acd.application.agent.execute_plan import (
    approve_plan,
    execute_plan,
    get_execution_status,
)


def test_execute_plan_success():
    """Executes an already approved plan successfully."""

    plan = SimpleNamespace(
        approved_by_user=True,
    )

    repository = MagicMock()
    repository.get_plan.side_effect = [plan, plan]

    orchestrator = MagicMock()

    execution_service = MagicMock()
    execution_service.execute_plan.return_value = {
        "success": True,
        "tasks_executed": 4,
        "tasks_failed": 2,
    }

    result = execute_plan(
        10,
        repository=repository,
        orchestrator=orchestrator,
        execution_service=execution_service,
    )

    assert result == {
        "success": True,
        "plan_id": 10,
        "tasks_executed": 4,
        "tasks_failed": 2,
        "total_tasks": 6,
    }

    execution_service.execute_plan.assert_called_once_with(
        10,
        orchestrator,
    )

    assert repository.get_plan.call_count == 2
    repository.approve_plan.assert_not_called()


def test_execute_plan_returns_error_when_plan_not_found():
    """Returns an error when the requested plan does not exist."""

    repository = MagicMock()
    repository.get_plan.return_value = None

    orchestrator = MagicMock()
    execution_service = MagicMock()

    result = execute_plan(
        999,
        repository=repository,
        orchestrator=orchestrator,
        execution_service=execution_service,
    )

    assert result == {
        "success": False,
        "error": "Plan not found",
    }

    execution_service.execute_plan.assert_not_called()





def test_execute_plan_approves_plan_before_execution():
    """Approves the plan before executing it."""

    plan_before = SimpleNamespace(approved_by_user=False)
    plan_after = SimpleNamespace(approved_by_user=True)

    repository = MagicMock()
    repository.get_plan.side_effect = [plan_before, plan_after]

    orchestrator = MagicMock()

    execution_service = MagicMock()
    execution_service.execute_plan.return_value = {
        "success": True,
        "tasks_executed": 1,
        "tasks_failed": 0,
    }

    result = execute_plan(
        5,
        approved=True,
        repository=repository,
        orchestrator=orchestrator,
        execution_service=execution_service,
    )

    repository.approve_plan.assert_called_once_with(
        5,
        approved=True,
    )

    assert result["success"] is True


def test_execute_plan_requires_approval():
    """Returns an error when the plan is still not approved."""

    plan = SimpleNamespace(
        approved_by_user=False,
    )

    repository = MagicMock()
    repository.get_plan.side_effect = [plan, plan]

    orchestrator = MagicMock()
    execution_service = MagicMock()

    result = execute_plan(
        10,
        repository=repository,
        orchestrator=orchestrator,
        execution_service=execution_service,
    )

    assert result == {
        "success": False,
        "error": "Plan requires approval",
        "plan_id": 10,
    }

    execution_service.execute_plan.assert_not_called()


def test_execute_plan_creates_default_dependencies():
    """Creates default collaborators when none are supplied."""

    repository = MagicMock()

    approved_plan = SimpleNamespace(
        approved_by_user=True,
    )

    repository.get_plan.side_effect = [
        approved_plan,
        approved_plan,
    ]

    orchestrator = MagicMock()

    execution_service = MagicMock()
    execution_service.execute_plan.return_value = {
        "success": True,
    }

    with (
        patch(
            "acd.application.agent.execute_plan.AgentRepository",
            return_value=repository,
        ),
        patch(
            "acd.application.agent.execute_plan.DefaultToolRegistry",
            return_value=MagicMock(),
        ),
        patch(
            "acd.application.agent.execute_plan.AIOrchestrator",
            return_value=orchestrator,
        ),
        patch(
            "acd.application.agent.execute_plan.AIExecutionService",
            return_value=execution_service,
        ),
    ):
        execute_plan(1)


def test_approve_plan_success():
    """Approves a plan successfully."""

    plan = SimpleNamespace(
        approval_status="approved",
    )

    repository = MagicMock()
    repository.approve_plan.return_value = plan

    result = approve_plan(
        7,
        repository=repository,
    )

    assert result == {
        "success": True,
        "plan_id": 7,
        "status": "approved",
    }

    repository.approve_plan.assert_called_once_with(
        7,
        approved=True,
    )


def test_approve_plan_returns_error_when_plan_not_found():
    """Returns an error when approving a nonexistent plan."""

    repository = MagicMock()
    repository.approve_plan.return_value = None

    result = approve_plan(
        99,
        repository=repository,
    )

    assert result == {
        "success": False,
        "error": "Plan not found",
    }


def test_approve_plan_creates_default_repository():
    """Creates the default repository when one is not supplied."""

    repository = MagicMock()

    repository.approve_plan.return_value = SimpleNamespace(
        approval_status="approved",
    )

    with patch(
        "acd.application.agent.execute_plan.AgentRepository",
        return_value=repository,
    ):
        result = approve_plan(3)

    assert result["success"] is True


def test_get_execution_status_with_service():
    """Uses the injected execution service."""

    execution_service = MagicMock()

    execution_service.get_execution_status.return_value = {
        "status": "running",
    }

    result = get_execution_status(
        15,
        execution_service=execution_service,
    )

    assert result == {
        "status": "running",
    }

    execution_service.get_execution_status.assert_called_once_with(15)


def test_get_execution_status_creates_default_service():
    """Creates the default execution service."""

    execution_service = MagicMock()

    execution_service.get_execution_status.return_value = {
        "status": "completed",
    }

    with patch(
        "acd.application.agent.execute_plan.AIExecutionService",
        return_value=execution_service,
    ):
        result = get_execution_status(1)

    assert result == {
        "status": "completed",
    }


