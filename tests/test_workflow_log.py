from __future__ import annotations

from acd.domain.entities.workflow_log import WorkflowLog


def test_workflow_log_creation():
    """WorkflowLog should initialize correctly."""

    log = WorkflowLog(
        workflow_execution_id=10,
    )

    assert log.workflow_execution_id == 10

    # Defaults do SQLAlchemy só são aplicados após persistência.
    assert log.level is None
    assert log.message is None
    assert log.created_at is None


def test_workflow_log_custom_values():
    """WorkflowLog should preserve explicitly supplied values."""

    log = WorkflowLog(
        workflow_execution_id=20,
        level="error",
        message="Workflow failed.",
    )

    assert log.workflow_execution_id == 20
    assert log.level == "error"
    assert log.message == "Workflow failed."


def test_workflow_log_table_name():
    """WorkflowLog should expose the expected table name."""

    assert WorkflowLog.__tablename__ == "workflow_logs"


def test_workflow_log_has_primary_key():
    """WorkflowLog should expose an id attribute."""

    log = WorkflowLog(
        workflow_execution_id=1,
    )

    assert hasattr(log, "id")


def test_workflow_log_foreign_key_value():
    """WorkflowLog should preserve workflow_execution_id."""

    log = WorkflowLog(
        workflow_execution_id=999,
    )

    assert log.workflow_execution_id == 999


def test_workflow_log_created_at_is_none_before_persist():
    """created_at should not be populated before persistence."""

    log = WorkflowLog(
        workflow_execution_id=1,
    )

    assert log.created_at is None


def test_workflow_log_accepts_empty_message():
    """WorkflowLog should accept an empty message."""

    log = WorkflowLog(
        workflow_execution_id=1,
        message="",
    )

    assert log.message == ""


def test_workflow_log_accepts_different_levels():
    """WorkflowLog should preserve different log levels."""

    for level in ("debug", "info", "warning", "error", "critical"):
        log = WorkflowLog(
            workflow_execution_id=1,
            level=level,
            message="Test",
        )

        assert log.level == level