from __future__ import annotations

import json
from typing import Any

from acd.domain.entities.workflow import Workflow
from acd.infrastructure.repositories.workflow_repository import WorkflowRepository
from acd.infrastructure.workflow.workflow_event_bus import EventBus
from acd.infrastructure.workflow.workflow_runner import WorkflowRunner


class WorkflowService:
    """Service for workflow management."""

    def __init__(
        self,
        repository: WorkflowRepository | None = None,
        runner: WorkflowRunner | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.repository = repository or WorkflowRepository()
        self.event_bus = event_bus or EventBus()
        self.runner = runner or WorkflowRunner(self.repository, self.event_bus)

    def create_workflow(
        self, name: str, description: str, steps: list[dict[str, Any]], *, version: str = "1"
    ) -> Workflow:
        """Create a new workflow."""
        definition = {"steps": steps}
        return self.repository.create_workflow(
            name, description, json.dumps(definition), version=version
        )

    def execute_workflow(
        self, workflow_id: int, application_id: int | None = None
    ) -> dict[str, Any]:
        """Execute a workflow."""
        execution = self.repository.create_execution(workflow_id, application_id)
        return self.runner.run(execution)

    def get_workflow(self, workflow_id: int) -> Workflow | None:
        """Get a workflow by ID."""
        return self.repository.get_workflow(workflow_id)

    def list_workflows(self) -> list[Workflow]:
        """List all workflows."""
        return self.repository.list_workflows()

    def get_execution_status(self, execution_id: int) -> dict[str, Any]:
        """Get execution status."""
        execution = self.repository.get_execution(execution_id)
        if execution is None:
            return {"status": "not_found"}
        return {
            "status": execution.status,
            "workflow_id": execution.workflow_id,
            "current_step": execution.current_step,
            "started_at": str(execution.started_at) if execution.started_at else None,
            "finished_at": str(execution.finished_at) if execution.finished_at else None,
        }
