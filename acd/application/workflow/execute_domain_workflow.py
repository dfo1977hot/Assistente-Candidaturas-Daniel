"""Application use case for executing registered domain workflow definitions."""

from __future__ import annotations

from typing import Any

from acd.domain.workflow.workflow_executor import WorkflowExecutionResult, WorkflowExecutor
from acd.domain.workflow.workflow_registry import WorkflowRegistry


def execute_domain_workflow(
    registry: WorkflowRegistry,
    executor: WorkflowExecutor,
    *,
    workflow_id: str,
    context: dict[str, Any] | None = None,
) -> WorkflowExecutionResult:
    """Find a registered workflow definition and execute it through the domain engine."""
    definition = registry.get(workflow_id)
    if definition is None:
        raise LookupError(f"Workflow '{workflow_id}' is not registered.")
    return executor.execute(definition, context)
