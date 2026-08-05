"""Domain abstraction for a workflow business step."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WorkflowStepState(StrEnum):
    """Lifecycle states of a workflow step."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


@dataclass
class WorkflowStep:
    """Represents a business step independently from its execution mechanism."""

    step_id: str
    name: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    timeout_seconds: int | None = None
    state: WorkflowStepState = WorkflowStepState.PENDING
    result: Any | None = None
    rollback_handler: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
