"""Lifecycle domain events for the workflow engine."""

from __future__ import annotations

from typing import Any

from acd.core.kernel.events import DomainEvent, EventType


class WorkflowLifecycleEvent(DomainEvent):
    """Base event emitted for a workflow lifecycle transition."""

    def __init__(
        self,
        name: str,
        workflow_id: str,
        execution_id: str,
        **payload: Any,
    ) -> None:
        """Create a lifecycle event with its workflow identity."""
        super().__init__(
            event_type=EventType.WORKFLOW,
            name=name,
            payload={"workflow_id": workflow_id, "execution_id": execution_id, **payload},
        )


class WorkflowStarted(WorkflowLifecycleEvent):
    """Signals that a workflow execution started."""

    def __init__(self, workflow_id: str, execution_id: str) -> None:
        super().__init__("workflow_started", workflow_id, execution_id)


class WorkflowCompleted(WorkflowLifecycleEvent):
    """Signals that a workflow execution completed."""

    def __init__(self, workflow_id: str, execution_id: str) -> None:
        super().__init__("workflow_completed", workflow_id, execution_id)


class WorkflowFailed(WorkflowLifecycleEvent):
    """Signals that a workflow execution failed."""

    def __init__(self, workflow_id: str, execution_id: str, reason: str) -> None:
        super().__init__("workflow_failed", workflow_id, execution_id, reason=reason)


class WorkflowPaused(WorkflowLifecycleEvent):
    """Signals that a workflow execution was paused."""

    def __init__(self, workflow_id: str, execution_id: str) -> None:
        super().__init__("workflow_paused", workflow_id, execution_id)


class WorkflowCancelled(WorkflowLifecycleEvent):
    """Signals that a workflow execution was cancelled."""

    def __init__(self, workflow_id: str, execution_id: str) -> None:
        super().__init__("workflow_cancelled", workflow_id, execution_id)
