from __future__ import annotations

from enum import Enum


class WorkflowState(Enum):
    """Estados possíveis de um workflow."""

    CREATED = "created"
    READY = "ready"
    EXECUTING = "executing"
    PAUSED = "paused"
    AWAITING_USER = "awaiting_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
