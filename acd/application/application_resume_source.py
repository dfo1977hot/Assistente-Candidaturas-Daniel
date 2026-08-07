"""Application-safe representation of the selected resume source."""

from __future__ import annotations

from enum import StrEnum


class ApplicationResumeSource(StrEnum):
    """Source used by an application without duplicating persisted state."""

    ORIGINAL = "original"
    RESUME_VERSION = "resume_version"

    @classmethod
    def from_selection(cls, selected_resume_version_id: int | None) -> ApplicationResumeSource:
        """Derive the source exclusively from the persisted selected version identifier."""
        if selected_resume_version_id is None:
            return cls.ORIGINAL
        return cls.RESUME_VERSION
