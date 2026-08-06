"""Write contract for the resume source selected by an application."""

from __future__ import annotations

from typing import Protocol


class ApplicationResumeSelectionPort(Protocol):
    """Persists only an application's selected resume version identifier."""

    def set_selected_resume_version(
        self, application_id: int, resume_version_id: int
    ) -> bool:
        """Set the selected resume version for an existing application."""

    def clear_selected_resume_version(self, application_id: int) -> bool:
        """Clear the selected resume version for an existing application."""
