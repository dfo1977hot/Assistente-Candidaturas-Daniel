from __future__ import annotations

from acd.application.intelligent_application_pipeline_events import (
    PipelineCancelled,
    PipelineCompleted,
    PipelineStarted,
    StageCompleted,
    StageFailed,
    StageStarted,
    create_pipeline_event,
)
from acd.core.kernel.events import EventType


def test_pipeline_events_are_auditable() -> None:
    event = create_pipeline_event(
        PipelineStarted,
        execution_id="execution-1",
        name="pipeline.started",
        payload={"application_id": 10},
    )

    assert event.event_type is EventType.PIPELINE
    assert event.execution_id == "execution-1"
    assert event.timestamp.tzinfo is not None


def test_all_pipeline_event_contracts_are_available() -> None:
    event_types = {
        PipelineStarted,
        StageStarted,
        StageCompleted,
        StageFailed,
        PipelineCompleted,
        PipelineCancelled,
    }

    assert len(event_types) == 6
