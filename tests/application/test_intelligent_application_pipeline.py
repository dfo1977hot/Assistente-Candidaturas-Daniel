from __future__ import annotations

from acd.application.intelligent_application_pipeline import (
    IntelligentApplicationPipeline,
    PipelineStage,
)


def test_pipeline_executes_enabled_stages_in_order() -> None:
    calls: list[str] = []
    pipeline = IntelligentApplicationPipeline(
        [
            PipelineStage("analysis", lambda context: calls.append(context["job"])),
            PipelineStage("ats", lambda context: {"score": 90}),
        ]
    )

    results = pipeline.run({"job": "Engineer"})

    assert calls == ["Engineer"]
    assert [result.status for result in results] == ["completed", "completed"]
    assert results[1].result == {"score": 90}
    assert results[0].duration_seconds >= 0


def test_pipeline_records_disabled_stage() -> None:
    pipeline = IntelligentApplicationPipeline(
        [PipelineStage("analysis", lambda context: context, enabled=False)]
    )

    results = pipeline.run({})

    assert results[0].status == "skipped"
    assert results[0].diagnosis == "Stage disabled."


def test_pipeline_stops_after_failed_stage() -> None:
    def fail(_: dict[str, object]) -> None:
        raise ValueError("Missing curriculum")

    pipeline = IntelligentApplicationPipeline(
        [
            PipelineStage("analysis", fail),
            PipelineStage("ats", lambda context: context),
        ]
    )

    results = pipeline.run({})

    assert len(results) == 1
    assert results[0].status == "failed"
    assert results[0].diagnosis == "Missing curriculum"
