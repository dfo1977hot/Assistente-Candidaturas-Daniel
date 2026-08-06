from __future__ import annotations

from acd.application.intelligent_application_pipeline_observability import (
    PipelineObservability,
)


def test_observability_records_trace_metrics_and_sinks() -> None:
    logs: list[tuple[str, dict[str, object]]] = []
    telemetry: list[dict[str, object]] = []
    observability = PipelineObservability(
        execution_id="execution-1",
        log_sink=lambda message, record: logs.append((message, record)),
        telemetry_sink=telemetry.append,
    )

    observability.record_stage("ats", 0.5, "completed")
    observability.complete("completed")

    assert observability.trace[0]["execution_id"] == "execution-1"
    assert observability.metrics["pipeline.stage.ats.duration_seconds"] == 0.5
    assert logs[0][0] == "pipeline.stage"
    assert telemetry[1]["status"] == "completed"
