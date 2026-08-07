from __future__ import annotations

import json
import logging
import time
from typing import Any

from acd.domain.entities.workflow_execution import WorkflowExecution
from acd.domain.workflow.execution_context import ExecutionContext
from acd.domain.workflow.workflow_state import WorkflowState
from acd.infrastructure.repositories.workflow_repository import WorkflowRepository
from acd.infrastructure.workflow.command_dispatcher import CommandDispatcher
from acd.infrastructure.workflow.workflow_event_bus import EventBus
from acd.observability import log_event, sanitize_text

logger = logging.getLogger(__name__)


class WorkflowRunner:
    """Executes a workflow step by step."""

    def __init__(
        self,
        repository: WorkflowRepository | None = None,
        event_bus: EventBus | None = None,
        dispatcher: CommandDispatcher | None = None,
    ) -> None:
        self.repository = repository or WorkflowRepository()
        self.event_bus = event_bus or EventBus()
        self.dispatcher = dispatcher or CommandDispatcher()

    def run(self, execution: WorkflowExecution) -> dict[str, Any]:
        """Execute a workflow."""
        started_at = time.perf_counter()
        workflow = self.repository.get_workflow(execution.workflow_id)
        if workflow is None:
            return {"status": "error", "message": "Workflow not found"}

        try:
            definition = json.loads(workflow.definition)
        except (json.JSONDecodeError, ValueError):
            return {"status": "error", "message": "Invalid workflow definition"}

        context = ExecutionContext(
            workflow_execution_id=execution.id,
            workflow_id=execution.workflow_id,
            application_id=execution.application_id,
        )

        execution.status = WorkflowState.EXECUTING.value
        log_event(
            logger,
            logging.INFO,
            "workflow.execution.started",
            "Workflow execution started",
            status="started",
            component="workflow",
            execution_id=execution.id,
            workflow_id=execution.workflow_id,
        )
        self.event_bus.publish(
            "workflow_started", {"execution_id": execution.id, "workflow_id": execution.workflow_id}
        )
        self.repository.create_log(execution.id, "info", "Workflow started")

        steps = definition.get("steps", [])
        for step_index, step in enumerate(steps):
            if execution.status in [WorkflowState.CANCELED.value, WorkflowState.FAILED.value]:
                break

            execution.current_step = step_index
            step_name = sanitize_text(step.get("name", f"step_{step_index}"))
            command_name = sanitize_text(step.get("command", ""))

            self.event_bus.publish(
                "step_started", {"execution_id": execution.id, "step_name": step_name}
            )
            self.repository.create_log(
                execution.id, "info", f"Step {step_index}: {step_name} started"
            )

            command = self.dispatcher.dispatch(command_name)
            if command is None:
                error_msg = f"Command {command_name} not found"
                execution.status = WorkflowState.FAILED.value
                self.repository.create_log(execution.id, "error", error_msg)
                self.event_bus.publish(
                    "step_failed",
                    {"execution_id": execution.id, "step_name": step_name, "error": error_msg},
                )
                break

            try:
                result = command.execute(context)
                self.event_bus.publish(
                    "step_completed",
                    {"execution_id": execution.id, "step_name": step_name, "result": result},
                )
                self.repository.create_log(
                    execution.id,
                    "info",
                    f"Step {step_index}: {step_name} completed ({type(result).__name__})",
                )
            except Exception as exc:
                error_msg = sanitize_text(str(exc))
                execution.status = WorkflowState.FAILED.value
                self.repository.create_log(
                    execution.id, "error", f"Step {step_index}: {step_name} failed: {error_msg}"
                )
                self.event_bus.publish(
                    "step_failed",
                    {"execution_id": execution.id, "step_name": step_name, "error": error_msg},
                )
                break

        if execution.status == WorkflowState.EXECUTING.value:
            execution.status = WorkflowState.COMPLETED.value
            self.event_bus.publish(
                "workflow_completed",
                {"execution_id": execution.id, "workflow_id": execution.workflow_id},
            )
            self.repository.create_log(execution.id, "info", "Workflow completed successfully")

        execution.result = json.dumps(context.data)
        self.repository.update_execution(execution)

        log_event(
            logger,
            logging.INFO
            if execution.status == WorkflowState.COMPLETED.value
            else logging.ERROR,
            "workflow.execution.completed"
            if execution.status == WorkflowState.COMPLETED.value
            else "workflow.execution.failed",
            "Workflow execution finished",
            status=execution.status,
            component="workflow",
            execution_id=execution.id,
            workflow_id=execution.workflow_id,
            duration_ms=(time.perf_counter() - started_at) * 1000,
        )

        return {"status": execution.status, "execution_id": execution.id, "result": context.data}
