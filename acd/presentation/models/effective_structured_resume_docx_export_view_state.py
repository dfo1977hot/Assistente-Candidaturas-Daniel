"""UI-safe outcome of an explicit DOCX export."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EffectiveStructuredResumeDocxExportViewState:
    """Immutable feedback for a completed DOCX export request."""

    status: str
    application_id: int
    is_success: bool
    destination_path: Path
    source: str
    message: str
