from __future__ import annotations

import pytest

from acd.core.kernel.events import EventType
from acd.domain.workflow.workflow_events import (
    WorkflowCancelled,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowLifecycleEvent,
    WorkflowPaused,
    WorkflowStarted,
)


@pytest.mark.parametrize(
    ("event", "name"),
    [
        (WorkflowStarted("application-v1", "run-1"), "workflow_started"),
        (WorkflowCompleted("application-v1", "run-1"), "workflow_completed"),
        (WorkflowPaused("application-v1", "run-1"), "workflow_paused"),
        (WorkflowCancelled("application-v1", "run-1"), "workflow_cancelled"),
    ],
)
def test_workflow_lifecycle_events_identify_the_execution(
    event: WorkflowLifecycleEvent, name: str
) -> None:
    """Lifecycle events retain their type and workflow execution identity."""
    assert event.event_type is EventType.WORKFLOW
    assert event.name == name
    assert event.payload == {"workflow_id": "application-v1", "execution_id": "run-1"}


def test_workflow_failed_includes_failure_reason() -> None:
    """Failure events retain the reason that ended execution."""
    event = WorkflowFailed("application-v1", "run-1", "Handler unavailable")

    assert event.payload["reason"] == "Handler unavailable"
