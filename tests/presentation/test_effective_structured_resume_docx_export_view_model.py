"""Pure Presentation tests for effective structured resume DOCX export."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from acd.application.effective_structured_resume_docx_export import (
    EffectiveStructuredResumeDocxExportStatus,
    ExportEffectiveStructuredResumeDocxResult,
)
from acd.presentation.models.effective_structured_resume_docx_export_view_state import (
    EffectiveStructuredResumeDocxExportViewState,
)
from acd.presentation.pages.effective_structured_resume_docx_export_view_model import (
    EffectiveStructuredResumeDocxExportViewModel,
)


class _UseCase:
    def __init__(self, result: ExportEffectiveStructuredResumeDocxResult) -> None:
        self.result = result
        self.requests: list[object] = []

    def execute(self, request: object) -> ExportEffectiveStructuredResumeDocxResult:
        self.requests.append(request)
        return self.result


@pytest.mark.parametrize("status", tuple(EffectiveStructuredResumeDocxExportStatus))
def test_view_model_maps_all_application_statuses(status) -> None:
    destination = Path("currículos") / "Daniel.docx"
    use_case = _UseCase(
        ExportEffectiveStructuredResumeDocxResult(
            status, 42, destination, status is EffectiveStructuredResumeDocxExportStatus.SUCCESS, "ok"
        )
    )

    state = EffectiveStructuredResumeDocxExportViewModel(use_case).export(42, destination)

    assert use_case.requests[0].application_id == 42
    assert use_case.requests[0].destination_path == destination
    assert state.status == status.value
    assert state.destination_path == destination


def test_view_state_is_immutable_and_contains_only_ui_safe_fields() -> None:
    state = EffectiveStructuredResumeDocxExportViewState(
        "success", 42, True, Path("resume.docx"), "original", "ok"
    )

    assert tuple(field.name for field in fields(state)) == (
        "status", "application_id", "is_success", "destination_path", "source", "message"
    )
    with pytest.raises(FrozenInstanceError):
        state.message = "changed"  # type: ignore[misc]


def test_view_model_has_no_presentation_or_infrastructure_dependency() -> None:
    source = __import__(
        "inspect"
    ).getsource(EffectiveStructuredResumeDocxExportViewModel)

    for forbidden in ("PySide6", "acd.infrastructure", "docx", "QFileDialog"):
        assert forbidden not in source
