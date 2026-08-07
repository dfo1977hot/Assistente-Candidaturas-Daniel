from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any

StageExecutor = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True, slots=True)
class PipelineStage:
    """An injectable application-pipeline stage."""

    name: str
    execute: StageExecutor
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class PipelineStageResult:
    """Outcome produced for one pipeline stage."""

    name: str
    status: str
    result: Any | None
    duration_seconds: float
    diagnosis: str


class IntelligentApplicationPipeline:
    """Coordinates enabled application stages in their declared order."""

    def __init__(self, stages: list[PipelineStage]) -> None:
        self._stages = stages

    def run(
        self, context: dict[str, Any], *, start_index: int = 0
    ) -> list[PipelineStageResult]:
        """Execute stages until one fails, returning a result for each visited stage."""

        if not 0 <= start_index <= len(self._stages):
            raise ValueError("Start index must reference a pipeline stage.")

        results: list[PipelineStageResult] = []

        for stage in self._stages[start_index:]:
            if not stage.enabled:
                results.append(
                    PipelineStageResult(
                        name=stage.name,
                        status="skipped",
                        result=None,
                        duration_seconds=0.0,
                        diagnosis="Stage disabled.",
                    )
                )
                continue

            started_at = perf_counter()
            try:
                result = stage.execute(context)
            except Exception as error:
                results.append(
                    PipelineStageResult(
                        name=stage.name,
                        status="failed",
                        result=None,
                        duration_seconds=perf_counter() - started_at,
                        diagnosis=str(error),
                    )
                )
                break

            results.append(
                PipelineStageResult(
                    name=stage.name,
                    status="completed",
                    result=result,
                    duration_seconds=perf_counter() - started_at,
                    diagnosis="Stage completed.",
                )
            )

        return results
