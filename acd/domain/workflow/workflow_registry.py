"""In-memory catalog for workflow business definitions."""

from __future__ import annotations

from acd.domain.workflow.workflow_definition import WorkflowDefinition


class WorkflowRegistry:
    """Registers workflow definitions and makes them discoverable by identifier."""

    def __init__(self) -> None:
        self._definitions: dict[str, WorkflowDefinition] = {}

    def register(self, definition: WorkflowDefinition) -> None:
        """Register or replace a workflow definition by its stable identifier."""
        self._definitions[definition.workflow_id] = definition

    def get(self, workflow_id: str) -> WorkflowDefinition | None:
        """Return a workflow definition when it is registered."""
        return self._definitions.get(workflow_id)

    def list_all(self) -> tuple[WorkflowDefinition, ...]:
        """Return every registered workflow definition in registration order."""
        return tuple(self._definitions.values())
