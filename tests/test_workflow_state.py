from __future__ import annotations

from acd.domain.workflow.workflow_state import WorkflowState


def test_workflow_state_values():
    """WorkflowState must expose all expected values."""

    assert WorkflowState.CREATED.value == "created"
    assert WorkflowState.READY.value == "ready"
    assert WorkflowState.EXECUTING.value == "executing"
    assert WorkflowState.PAUSED.value == "paused"
    assert WorkflowState.AWAITING_USER.value == "awaiting_user"
    assert WorkflowState.COMPLETED.value == "completed"
    assert WorkflowState.FAILED.value == "failed"
    assert WorkflowState.CANCELED.value == "canceled"


def test_workflow_state_is_enum():
    """WorkflowState must behave like an enum."""

    assert WorkflowState("created") is WorkflowState.CREATED
    assert WorkflowState("completed") is WorkflowState.COMPLETED


def test_workflow_state_iteration_order():
    """WorkflowState should preserve the declared members."""

    members = [state.name for state in WorkflowState]

    assert members == [
        "CREATED",
        "READY",
        "EXECUTING",
        "PAUSED",
        "AWAITING_USER",
        "COMPLETED",
        "FAILED",
        "CANCELED",
    ]


def test_workflow_state_member_count():
    """WorkflowState should contain the expected number of members."""

    assert len(list(WorkflowState)) == 8