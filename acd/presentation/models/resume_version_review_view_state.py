"""Presentation-safe state for the read-only resume version review."""

from __future__ import annotations

from dataclasses import dataclass

from acd.application.application_resume_source import ApplicationResumeSource


@dataclass(frozen=True)
class ResumeVersionItemViewState:
    """One persisted version available in the selector."""

    version_id: int
    label: str


@dataclass(frozen=True)
class ResumeVersionReviewViewState:
    """Immutable content rendered by ``ResumeVersionReviewPanel``."""

    status: str
    title: str
    message: str
    application_id: int
    original_content: str = ""
    versions: tuple[ResumeVersionItemViewState, ...] = ()
    selected_version_id: int | None = None
    selected_content: str = ""
    explanation: str = ""
    resume_source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL
    selected_resume_version_id: int | None = None
