from __future__ import annotations

from acd.domain.entities.workflow_event import WorkflowEvent


def test_workflow_event_creation():
    """WorkflowEvent should initialize correctly."""

    event = WorkflowEvent(
        workflow_execution_id=10,
        event_type="workflow_started",
    )

    assert event.workflow_execution_id == 10
    assert event.event_type == "workflow_started"

    # Defaults do SQLAlchemy são aplicados somente após persistência.
    assert event.event_data is None
    assert event.created_at is None


def test_workflow_event_custom_values():
    """WorkflowEvent should preserve explicitly supplied values."""

    event = WorkflowEvent(
        workflow_execution_id=20,
        event_type="step_completed",
        event_data='{"step": 1}',
    )

    assert event.workflow_execution_id == 20
    assert event.event_type == "step_completed"
    assert event.event_data == '{"step": 1}'


def test_workflow_event_table_name():
    """WorkflowEvent should expose the expected table name."""

    assert WorkflowEvent.__tablename__ == "workflow_events"


def test_workflow_event_has_primary_key():
    """WorkflowEvent should expose an id attribute."""

    event = WorkflowEvent(
        workflow_execution_id=1,
        event_type="created",
    )

    assert hasattr(event, "id")


def test_workflow_event_foreign_key_value():
    """WorkflowEvent should preserve workflow_execution_id."""

    event = WorkflowEvent(
        workflow_execution_id=999,
        event_type="created",
    )

    assert event.workflow_execution_id == 999


def test_workflow_event_created_at_is_none_before_persist():
    """created_at should not be populated before persistence."""

    event = WorkflowEvent(
        workflow_execution_id=1,
        event_type="created",
    )

    assert event.created_at is None