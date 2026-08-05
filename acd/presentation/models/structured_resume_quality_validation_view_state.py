"""UI-safe state for structured resume quality validation."""

from __future__ import annotations

from dataclasses import dataclass

from acd.application.structured_resume_quality_validation import StructuredResumeQualityIssue


@dataclass(frozen=True)
class StructuredResumeQualityValidationViewState:
    """Immutable read-only feedback displayed after validation."""

    status: str
    application_id: int
    is_success: bool
    is_valid: bool
    score: int
    issues: tuple[StructuredResumeQualityIssue, ...]
    error_count: int
    warning_count: int
    info_count: int
    summary: str
    message: str
