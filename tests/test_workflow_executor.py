from __future__ import annotations

from typing import Any

from acd.core.kernel.event_bus import EventBus
from acd.domain.workflow.workflow_definition import (
    WorkflowCategory,
    WorkflowDefinition,
)
from acd.domain.workflow.workflow_events import WorkflowCompleted, WorkflowStarted
from acd.domain.workflow.workflow_executor import WorkflowExecutor
from acd.domain.workflow.workflow_observability import WorkflowObservability
from acd.domain.workflow.workflow_stage import WorkflowStep


class AnalyzeJobHandler:
    """Test handler representing an existing application capability."""

    def execute(self, step: WorkflowStep, context: dict[str, Any]) -> dict[str, bool]:
        context["job_analyzed"] = True
        return {"analyzed": True}


def test_workflow_executor_delegates_steps_to_registered_handlers() -> None:
    """The executor orchestrates handlers without implementing their business logic."""
    definition = WorkflowDefinition(
        workflow_id="application-v1",
        name="Candidatura",
        description="Processo de candidatura para uma vaga.",
        version="1.0",
        category=WorkflowCategory.APPLICATION,
        steps=("analyze_job",),
    )
    executor = WorkflowExecutor(handlers={"analyze_job": AnalyzeJobHandler()})

    result = executor.execute(definition)

    assert result.status == "completed"
    assert result.execution_id
    assert result.context == {"job_analyzed": True}
    assert result.completed_steps == ("analyze_job",)
    assert result.observability is not None
    assert result.observability.checkpoint == "analyze_job"
    assert result.observability.statistics == {"completed_steps": 1, "failed_steps": 0}


def test_workflow_executor_rejects_an_unknown_step_handler() -> None:
    """A definition cannot execute a step that has no injected capability."""
    definition = WorkflowDefinition(
        workflow_id="application-v1",
        name="Candidatura",
        description="Processo de candidatura para uma vaga.",
        version="1.0",
        category=WorkflowCategory.APPLICATION,
        steps=("analyze_job",),
    )

    result = WorkflowExecutor().execute(definition)

    assert result.status == "failed"
    assert result.errors == ("No handler is registered for step 'analyze_job'.",)
    assert result.observability is not None
    assert result.observability.failed_steps == ["analyze_job"]


def test_workflow_observability_records_duration_after_completion() -> None:
    """Observability records are finalized with their duration and status."""
    observation = WorkflowObservability("application-v1")

    observation.complete("completed")

    assert observation.duration_seconds is not None
    assert observation.status == "completed"


def test_workflow_executor_publishes_lifecycle_events_to_kernel_bus() -> None:
    """The executor publishes typed lifecycle events through an injected event bus."""
    events: list[str] = []
    event_bus = EventBus()
    event_bus.subscribe(WorkflowStarted, lambda event: events.append(event.name))
    event_bus.subscribe(WorkflowCompleted, lambda event: events.append(event.name))
    definition = WorkflowDefinition(
        workflow_id="application-v1",
        name="Candidatura",
        description="Processo de candidatura para uma vaga.",
        version="1.0",
        category=WorkflowCategory.APPLICATION,
        steps=("analyze_job",),
    )

    WorkflowExecutor(
        handlers={"analyze_job": AnalyzeJobHandler()}, event_publisher=event_bus
    ).execute(definition, execution_id="run-1")

    assert events == ["workflow_started", "workflow_completed"]
