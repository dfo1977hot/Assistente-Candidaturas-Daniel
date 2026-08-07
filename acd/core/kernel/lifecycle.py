"""Application lifecycle."""

from __future__ import annotations

from enum import StrEnum


class LifecycleState(StrEnum):
    """Application lifecycle."""

    CREATED = "created"

    INITIALIZING = "initializing"

    READY = "ready"

    RUNNING = "running"

    STOPPING = "stopping"

    STOPPED = "stopped"