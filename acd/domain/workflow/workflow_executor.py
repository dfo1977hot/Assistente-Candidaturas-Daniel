"""Domain execution orchestration for workflow definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4

from acd.core.kernel.events import DomainEvent
from acd.domain.workflow.workflow_definition import WorkflowDefinition
from acd.domain.workflow.workflow_events import (
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from acd.domain.workflow.workflow_observability import WorkflowObservability
from acd.domain.workflow.workflow_stage import WorkflowStep, WorkflowStepState
from acd.domain.workflow.workflow_validation import WorkflowValidator


class WorkflowStepHandler(Protocol):
    """Executes one business step through an injected application service."""

    def execute(self, step: WorkflowStep, context: dict[str, Any]) -> Any:
        """Execute the business capability represented by a step."""


class WorkflowEventPublisher(Protocol):
    """Publishes workflow lifecycle events to an outer event mechanism."""

    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""


@dataclass(frozen=True)
class WorkflowExecutionResult:
    """Result produced when a workflow definition is executed."""

    status: str
    execution_id: str
    context: dict[str, Any]
    errors: tuple[str, ...] = ()
    completed_steps: tuple[str, ...] = ()
    observability: WorkflowObservability | None = None


@dataclass
class WorkflowExecutor:
    """Orchestrates registered step handlers without owning business capabilities."""

    handlers: dict[str, WorkflowStepHandler] = field(default_factory=dict)
    validator: WorkflowValidator = field(default_factory=WorkflowValidator)
    event_publisher: WorkflowEventPublisher | None = None

    def execute(
        self,
        definition: WorkflowDefinition,
        context: dict[str, Any] | None = None,
        observability: WorkflowObservability | None = None,
        execution_id: str | None = None,
    ) -> WorkflowExecutionResult:
        """Execute ordered steps using handlers supplied by an outer layer."""
        validation = self.validator.validate(definition)
        execution_context = dict(context or {})
        observation = observability or WorkflowObservability(definition.workflow_id)
        current_execution_id = execution_id or str(uuid4())
        self._publish(WorkflowStarted(definition.workflow_id, current_execution_id))
        if not validation.is_valid:
            observation.complete("failed")
            self._publish(
                WorkflowFailed(
                    definition.workflow_id,
                    current_execution_id,
                    "; ".join(validation.errors),
                )
            )
            return WorkflowExecutionResult(
                status="failed",
                execution_id=current_execution_id,
                context=execution_context,
                errors=validation.errors,
                observability=observation,
            )

        completed_steps: list[str] = []
        for item in definition.steps:
            step = self._as_step(item)
            observation.record_checkpoint(step.step_id)
            handler = self.handlers.get(step.step_id)
            if handler is None:
                step.state = WorkflowStepState.FAILED
                observation.record_failure(step.step_id)
                observation.complete("failed")
                error = f"No handler is registered for step '{step.step_id}'."
                self._publish(WorkflowFailed(definition.workflow_id, current_execution_id, error))
                return WorkflowExecutionResult(
                    status="failed",
                    execution_id=current_execution_id,
                    context=execution_context,
                    errors=(error,),
                    completed_steps=tuple(completed_steps),
                    observability=observation,
                )

            try:
                step.state = WorkflowStepState.RUNNING
                step.result = handler.execute(step, execution_context)
                step.state = WorkflowStepState.COMPLETED
                completed_steps.append(step.step_id)
                observation.record_completion(step.step_id)
            except Exception as error:
                step.state = WorkflowStepState.FAILED
                observation.record_failure(step.step_id)
                observation.complete("failed")
                self._publish(WorkflowFailed(definition.workflow_id, current_execution_id, str(error)))
                return WorkflowExecutionResult(
                    status="failed",
                    execution_id=current_execution_id,
                    context=execution_context,
                    errors=(str(error),),
                    completed_steps=tuple(completed_steps),
                    observability=observation,
                )

        observation.complete("completed")
        self._publish(WorkflowCompleted(definition.workflow_id, current_execution_id))
        return WorkflowExecutionResult(
            status="completed",
            execution_id=current_execution_id,
            context=execution_context,
            completed_steps=tuple(completed_steps),
            observability=observation,
        )

    @staticmethod
    def _as_step(item: str | WorkflowStep) -> WorkflowStep:
        if isinstance(item, WorkflowStep):
            return item
        return WorkflowStep(step_id=item, name=item)

    def _publish(self, event: DomainEvent) -> None:
        """Publish an event when an outer publisher has been configured."""
        if self.event_publisher is not None:
            self.event_publisher.publish(event)
