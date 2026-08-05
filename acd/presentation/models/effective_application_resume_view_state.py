"""Immutable Presentation state for an effective application resume preview."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EffectiveApplicationResumeViewState:
    """Read-only data rendered by the effective resume preview panel."""

    status: str
    application_id: int
    source_label: str
    version_label: str
    title: str
    content: str
    content_format: str
    message: str
    is_available: bool
    is_original: bool
    is_generated_version: bool
