from __future__ import annotations

from acd.domain.entities.workflow_execution import WorkflowExecution


def test_workflow_execution_creation():
    """WorkflowExecution should initialize correctly."""

    execution = WorkflowExecution(
        workflow_id=10,
        application_id=20,
    )

    assert execution.workflow_id == 10
    assert execution.application_id == 20

    # Defaults do SQLAlchemy são aplicados somente na persistência.
    assert execution.status is None
    assert execution.current_step is None
    assert execution.duration is None
    assert execution.result is None
    assert execution.context is None

    assert execution.started_at is None
    assert execution.finished_at is None
    assert execution.created_at is None


def test_workflow_execution_custom_values():
    """WorkflowExecution should preserve explicitly supplied values."""

    execution = WorkflowExecution(
        workflow_id=1,
        application_id=2,
        status="completed",
        current_step=5,
        duration=120,
        result='{"success": true}',
        context='{"step": 5}',
    )

    assert execution.status == "completed"
    assert execution.current_step == 5
    assert execution.duration == 120
    assert execution.result == '{"success": true}'
    assert execution.context == '{"step": 5}'


def test_workflow_execution_optional_fields():
    """Optional fields should default to None."""

    execution = WorkflowExecution(
        workflow_id=1,
    )

    assert execution.application_id is None
    assert execution.started_at is None
    assert execution.finished_at is None


def test_workflow_execution_tablename():
    """WorkflowExecution should expose the expected table name."""

    assert WorkflowExecution.__tablename__ == "workflow_executions"


def test_workflow_execution_primary_key():
    """WorkflowExecution should expose an id attribute."""

    execution = WorkflowExecution(
        workflow_id=1,
    )

    assert hasattr(execution, "id")


def test_workflow_execution_foreign_key():
    """WorkflowExecution should preserve workflow_id."""

    execution = WorkflowExecution(
        workflow_id=999,
    )

    assert execution.workflow_id == 999