from __future__ import annotations

from acd.application.intelligent_application_pipeline_progress import build_pipeline_progress
from acd.application.intelligent_application_pipeline_state import PipelineState


def test_progress_exposes_current_pipeline_information() -> None:
    state = PipelineState()
    state.start_stage("ats")
    state.update_progress(50)
    state.add_warning("Optional profile field missing")

    progress = build_pipeline_progress(state)

    assert progress.percentage == 50
    assert progress.current_stage == "ats"
    assert progress.estimated_total_seconds is not None
    assert progress.remaining_seconds is not None
    assert progress.messages == ("Optional profile field missing",)


def test_progress_has_no_estimate_before_progress_starts() -> None:
    progress = build_pipeline_progress(PipelineState())

    assert progress.estimated_total_seconds is None
    assert progress.remaining_seconds is None
