"""UI-facing state for explicit resume optimization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResumeOptimizationViewState:
    """Safe presentation projection of an optimization outcome."""

    application_id: int
    status: str
    title: str
    message: str
    success: bool
    version: str | None = None
