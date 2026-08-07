"""In-memory observability record for workflow execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class WorkflowObservability:
    """Records workflow execution timing, failures, checkpoints, and statistics."""

    workflow_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    status: str = "running"
    checkpoint: str | None = None
    completed_steps: list[str] = field(default_factory=list)
    failed_steps: list[str] = field(default_factory=list)

    def record_checkpoint(self, step_id: str) -> None:
        """Record the step currently being executed."""
        self.checkpoint = step_id

    def record_completion(self, step_id: str) -> None:
        """Record a successfully completed step."""
        self.completed_steps.append(step_id)

    def record_failure(self, step_id: str) -> None:
        """Record a failed step."""
        self.failed_steps.append(step_id)

    def complete(self, status: str) -> None:
        """Finalize the observation with the execution status."""
        self.status = status
        self.finished_at = datetime.now(UTC)

    @property
    def duration_seconds(self) -> float | None:
        """Return elapsed time when the execution has finished."""
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def statistics(self) -> dict[str, int]:
        """Return aggregate step counters for the execution."""
        return {
            "completed_steps": len(self.completed_steps),
            "failed_steps": len(self.failed_steps),
        }
