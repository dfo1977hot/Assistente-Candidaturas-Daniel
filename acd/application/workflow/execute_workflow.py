from __future__ import annotations

from typing import Any

from acd.services.workflow_service import WorkflowService


def execute_workflow(
    service: WorkflowService, *, workflow_id: int, application_id: int | None = None
) -> dict[str, Any]:
    """Execute a workflow."""
    return service.execute_workflow(workflow_id, application_id)
