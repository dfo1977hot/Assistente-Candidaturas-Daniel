from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from acd.core.kernel.events import DomainEvent, EventType


@dataclass(slots=True)
class PipelineEvent(DomainEvent):
    """Auditable base event for an intelligent application pipeline."""

    execution_id: str = ""


@dataclass(slots=True)
class PipelineStarted(PipelineEvent):
    """Signals that a pipeline execution has started."""


@dataclass(slots=True)
class StageStarted(PipelineEvent):
    """Signals that a pipeline stage has started."""


@dataclass(slots=True)
class StageCompleted(PipelineEvent):
    """Signals that a pipeline stage has completed."""


@dataclass(slots=True)
class StageFailed(PipelineEvent):
    """Signals that a pipeline stage has failed."""


@dataclass(slots=True)
class PipelineCompleted(PipelineEvent):
    """Signals that a pipeline execution has completed."""


@dataclass(slots=True)
class PipelineCancelled(PipelineEvent):
    """Signals that a pipeline execution has been cancelled."""


def create_pipeline_event(
    event_class: type[PipelineEvent],
    *,
    execution_id: str,
    name: str,
    payload: dict[str, Any],
) -> PipelineEvent:
    """Create a pipeline event with the canonical event category."""

    return event_class(
        event_type=EventType.PIPELINE,
        name=name,
        payload=payload,
        execution_id=execution_id,
    )
