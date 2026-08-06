from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass(slots=True)
class PipelineState:
    """Mutable execution state for an intelligent application pipeline."""

    status: str = "pending"
    progress: int = 0
    current_stage: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    partial_result: dict[str, Any] = field(default_factory=dict)
    checkpoint: dict[str, Any] = field(default_factory=dict)
    _started_at: float | None = field(default=None, init=False, repr=False)

    @property
    def elapsed_seconds(self) -> float:
        """Return elapsed execution time without persisting a clock value."""

        if self._started_at is None:
            return 0.0
        return perf_counter() - self._started_at

    def start_stage(self, stage: str) -> None:
        """Mark a stage as currently running."""

        if self._started_at is None:
            self._started_at = perf_counter()
        self.status = "running"
        self.current_stage = stage

    def update_progress(self, progress: int) -> None:
        """Update progress using a percentage between zero and one hundred."""

        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100.")
        self.progress = progress

    def add_result(self, name: str, result: Any) -> None:
        """Store a result that can be consumed by a subsequent stage."""

        self.partial_result[name] = result

    def add_error(self, message: str) -> None:
        """Record an execution error and mark the pipeline as failed."""

        self.errors.append(message)
        self.status = "failed"

    def add_warning(self, message: str) -> None:
        """Record a non-blocking execution warning."""

        self.warnings.append(message)

    def save_checkpoint(self, next_stage_index: int = 0) -> None:
        """Capture the current resumable execution boundary in memory."""

        self.checkpoint = {
            "current_stage": self.current_stage,
            "next_stage_index": next_stage_index,
            "progress": self.progress,
            "partial_result": self.partial_result.copy(),
        }
