from __future__ import annotations

import pytest

from acd.application.intelligent_application_pipeline_state import PipelineState


def test_pipeline_state_tracks_stage_progress_and_results() -> None:
    state = PipelineState()

    state.start_stage("ats")
    state.update_progress(40)
    state.add_result("ats", {"score": 90})
    state.save_checkpoint()

    assert state.status == "running"
    assert state.current_stage == "ats"
    assert state.elapsed_seconds >= 0
    assert state.checkpoint["progress"] == 40
    assert state.checkpoint["partial_result"] == {"ats": {"score": 90}}


def test_pipeline_state_records_warnings_and_errors() -> None:
    state = PipelineState()

    state.add_warning("Missing optional profile field")
    state.add_error("ATS service unavailable")

    assert state.warnings == ["Missing optional profile field"]
    assert state.errors == ["ATS service unavailable"]
    assert state.status == "failed"


def test_pipeline_state_rejects_invalid_progress() -> None:
    state = PipelineState()

    with pytest.raises(ValueError, match="between 0 and 100"):
        state.update_progress(101)
