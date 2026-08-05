from __future__ import annotations

from acd.domain.workflow.workflow_stage import WorkflowStep
from acd.infrastructure.workflow.workflow_step_handler import CommandDispatcherStepHandler


def test_command_dispatcher_step_handler_reuses_registered_command() -> None:
    """The adapter delegates execution to the existing command dispatcher."""
    context: dict[str, object] = {}
    handler = CommandDispatcherStepHandler()

    result = handler.execute(WorkflowStep("analyze_job", "Analisar vaga"), context)

    assert result == {"status": "success", "message": "Job analyzed"}
    assert context == {"job_analysis": {"analyzed": True}}
