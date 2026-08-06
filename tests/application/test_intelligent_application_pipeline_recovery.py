from __future__ import annotations

import pytest

from acd.application.intelligent_application_pipeline import (
    IntelligentApplicationPipeline,
    PipelineStage,
)
from acd.application.intelligent_application_pipeline_recovery import PipelineRecovery
from acd.application.intelligent_application_pipeline_state import PipelineState


def test_recovery_resumes_from_checkpoint_boundary() -> None:
    calls: list[str] = []
    pipeline = IntelligentApplicationPipeline(
        [
            PipelineStage("analysis", lambda context: calls.append("analysis")),
            PipelineStage("ats", lambda context: calls.append(context["analysis"])),
        ]
    )
    state = PipelineState()
    state.add_result("analysis", "done")
    state.save_checkpoint(next_stage_index=1)

    results = PipelineRecovery().resume(pipeline, {}, state)

    assert calls == ["done"]
    assert [result.name for result in results] == ["ats"]


def test_recovery_rejects_invalid_checkpoint() -> None:
    pipeline = IntelligentApplicationPipeline([])

    with pytest.raises(ValueError, match="checkpoint is invalid"):
        PipelineRecovery().resume(pipeline, {}, PipelineState())
