"""UI-safe state for one structured resume generation request."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StructuredResumeGenerationViewState:
    application_id: int
    status: str
    title: str
    message: str
    is_success: bool
    resume_version_id: int | None = None
    version: str | None = None
    explanation: str | None = None
