from __future__ import annotations

from acd.application.intelligent_application_pipeline import PipelineStageResult
from acd.application.intelligent_application_pipeline_diagnostics import (
    build_pipeline_diagnostics,
)
from acd.application.intelligent_application_pipeline_state import PipelineState


def test_diagnostics_collects_execution_information() -> None:
    state = PipelineState()
    state.start_stage("ats")
    state.add_warning("Optional profile field missing")
    state.add_result("ats", {"score": 91})

    diagnostics = build_pipeline_diagnostics(
        state,
        [
            PipelineStageResult("analysis", "completed", {}, 0.5, "Stage completed."),
            PipelineStageResult("ats", "failed", None, 0.2, "ATS unavailable"),
        ],
        rules_applied=("required-job-description",),
        services_used=("ATSService",),
    )

    assert diagnostics.stage_durations == {"analysis": 0.5, "ats": 0.2}
    assert diagnostics.failures == ("ATS unavailable",)
    assert diagnostics.warnings == ("Optional profile field missing",)
    assert diagnostics.rules_applied == ("required-job-description",)
    assert diagnostics.services_used == ("ATSService",)
    assert diagnostics.final_result == {"ats": {"score": 91}}


def test_diagnostics_includes_state_errors() -> None:
    state = PipelineState()
    state.add_error("Invalid application")

    diagnostics = build_pipeline_diagnostics(state, [])

    assert diagnostics.failures == ("Invalid application",)
