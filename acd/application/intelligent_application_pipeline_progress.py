from __future__ import annotations

from dataclasses import dataclass

from acd.application.intelligent_application_pipeline_state import PipelineState


@dataclass(frozen=True, slots=True)
class PipelineProgress:
    """Read-only progress information for internal pipeline consumers."""

    percentage: int
    current_stage: str | None
    elapsed_seconds: float
    estimated_total_seconds: float | None
    remaining_seconds: float | None
    messages: tuple[str, ...]


def build_pipeline_progress(state: PipelineState) -> PipelineProgress:
    """Build a progress snapshot from the current pipeline state."""

    elapsed_seconds = state.elapsed_seconds
    estimated_total_seconds: float | None = None
    remaining_seconds: float | None = None

    if state.progress > 0:
        estimated_total_seconds = elapsed_seconds * 100 / state.progress
        remaining_seconds = max(estimated_total_seconds - elapsed_seconds, 0.0)

    messages = (*state.warnings, *state.errors)
    return PipelineProgress(
        percentage=state.progress,
        current_stage=state.current_stage,
        elapsed_seconds=elapsed_seconds,
        estimated_total_seconds=estimated_total_seconds,
        remaining_seconds=remaining_seconds,
        messages=messages,
    )
