from __future__ import annotations

from typing import Callable

from acd.infrastructure.workflow.command import WorkflowCommand
from acd.infrastructure.workflow.commands import (
    AnalyzeJobCommand,
    GenerateResumeCommand,
    GenerateCoverLetterCommand,
    RunATSCommand,
    ApplyToJobCommand,
    RegisterApplicationCommand,
)


class CommandDispatcher:
    """Dispatches command names to command implementations."""

    def __init__(self) -> None:
        self._commands: dict[str, Callable[[], WorkflowCommand]] = {
            "analyze_job": AnalyzeJobCommand,
            "generate_resume": GenerateResumeCommand,
            "generate_cover_letter": GenerateCoverLetterCommand,
            "run_ats": RunATSCommand,
            "apply_to_job": ApplyToJobCommand,
            "register_application": RegisterApplicationCommand,
        }

    def register(self, name: str, command_class: type[WorkflowCommand]) -> None:
        """Register a command factory."""
        self._commands[name.lower().strip()] = command_class

    def dispatch(self, name: str) -> WorkflowCommand | None:
        """Dispatch and instantiate a command."""
        factory = self._commands.get(name.lower().strip())
        if factory is None:
            return None
        return factory()
