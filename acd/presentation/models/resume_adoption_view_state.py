"""Immutable Presentation state for explicit resume-source adoption."""

from __future__ import annotations

from dataclasses import dataclass

from acd.application.application_resume_source import ApplicationResumeSource


@dataclass(frozen=True)
class ResumeAdoptionViewState:
    """Rendered outcome of an explicit adoption command."""

    status: str
    application_id: int
    resume_source: ApplicationResumeSource
    selected_resume_version_id: int | None
    title: str
    message: str
