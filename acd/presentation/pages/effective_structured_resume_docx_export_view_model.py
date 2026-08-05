"""Presentation mapping for explicit effective structured DOCX export."""

from __future__ import annotations

from pathlib import Path

from acd.application.effective_structured_resume_docx_export import (
    ExportEffectiveStructuredResumeDocxRequest,
    ExportEffectiveStructuredResumeDocxUseCase,
)
from acd.presentation.models.effective_structured_resume_docx_export_view_state import (
    EffectiveStructuredResumeDocxExportViewState,
)


class EffectiveStructuredResumeDocxExportViewModel:
    """Run the read-only export use case without Presentation infrastructure access."""

    def __init__(self, use_case: ExportEffectiveStructuredResumeDocxUseCase) -> None:
        self._use_case = use_case

    def export(
        self, application_id: int, destination_path: str | Path
    ) -> EffectiveStructuredResumeDocxExportViewState:
        """Map one explicit filesystem export request to UI-safe feedback."""
        result = self._use_case.execute(
            ExportEffectiveStructuredResumeDocxRequest(application_id, Path(destination_path))
        )
        return EffectiveStructuredResumeDocxExportViewState(
            result.status.value,
            result.application_id,
            result.exported,
            result.destination_path,
            result.source.value,
            result.message,
        )
