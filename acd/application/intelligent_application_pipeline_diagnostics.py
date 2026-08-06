from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from acd.application.intelligent_application_pipeline import PipelineStageResult
from acd.application.intelligent_application_pipeline_state import PipelineState


@dataclass(frozen=True, slots=True)
class PipelineDiagnostics:
    """Immutable diagnostic summary of one pipeline execution."""

    total_duration_seconds: float
    stage_durations: dict[str, float]
    failures: tuple[str, ...]
    warnings: tuple[str, ...]
    rules_applied: tuple[str, ...]
    services_used: tuple[str, ...]
    final_result: dict[str, Any]


def build_pipeline_diagnostics(
    state: PipelineState,
    stage_results: list[PipelineStageResult],
    *,
    rules_applied: tuple[str, ...] = (),
    services_used: tuple[str, ...] = (),
) -> PipelineDiagnostics:
    """Build a diagnostic snapshot without mutating the execution state."""

    failures = [*state.errors]
    failures.extend(
        result.diagnosis for result in stage_results if result.status == "failed"
    )

    return PipelineDiagnostics(
        total_duration_seconds=state.elapsed_seconds,
        stage_durations={result.name: result.duration_seconds for result in stage_results},
        failures=tuple(failures),
        warnings=tuple(state.warnings),
        rules_applied=rules_applied,
        services_used=services_used,
        final_result=state.partial_result.copy(),
    )
