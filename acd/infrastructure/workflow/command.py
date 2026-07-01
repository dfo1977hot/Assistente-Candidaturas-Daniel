from __future__ import annotations

from abc import ABC, abstractmethod

from acd.domain.workflow.execution_context import ExecutionContext


class WorkflowCommand(ABC):
    """Abstract base class for workflow commands."""

    @abstractmethod
    def execute(self, context: ExecutionContext) -> dict[str, object]:
        """Execute the command."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Return command name."""
        ...
