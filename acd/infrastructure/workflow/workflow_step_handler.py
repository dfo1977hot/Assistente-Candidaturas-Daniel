"""Adapter that reuses legacy workflow commands from the domain workflow engine."""

from __future__ import annotations

from typing import Any

from acd.domain.workflow.execution_context import ExecutionContext
from acd.domain.workflow.workflow_stage import WorkflowStep
from acd.infrastructure.workflow.command_dispatcher import CommandDispatcher


class CommandDispatcherStepHandler:
    """Adapts registered workflow commands to the domain step-handler contract."""

    def __init__(self, dispatcher: CommandDispatcher | None = None) -> None:
        self._dispatcher = dispatcher or CommandDispatcher()

    def execute(self, step: WorkflowStep, context: dict[str, Any]) -> Any:
        """Delegate a step to its existing command and synchronize its context."""
        command_name = str(step.metadata.get("command", step.step_id))
        command = self._dispatcher.dispatch(command_name)
        if command is None:
            raise LookupError(f"Command '{command_name}' is not registered.")

        command_context = ExecutionContext(workflow_execution_id=0, workflow_id=0)
        command_context.data.update(context)
        result = command.execute(command_context)
        context.update(command_context.data)
        return result
