"""Presentation tests for the effective application resume preview."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.effective_application_resume_use_case import (
    EffectiveApplicationResumeResult,
    EffectiveApplicationResumeStatus,
)
from acd.presentation.effective_application_resume_preview_panel import (
    EffectiveApplicationResumePreviewPanel,
)
from acd.presentation.pages.effective_application_resume_view_model import (
    EffectiveApplicationResumeViewModel,
)


class _UseCase:
    def __init__(self, result: EffectiveApplicationResumeResult) -> None:
        self.result = result
        self.requests: list[int] = []

    def execute(self, request):
        self.requests.append(request.application_id)
        return self.result


def _result(source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL) -> EffectiveApplicationResumeResult:
    return EffectiveApplicationResumeResult(
        EffectiveApplicationResumeStatus.SUCCESS,
        7,
        4,
        source,
        None if source is ApplicationResumeSource.ORIGINAL else 3,
        None if source is ApplicationResumeSource.ORIGINAL else 3,
        "Currículo original" if source is ApplicationResumeSource.ORIGINAL else "Versão v3",
        "Conteúdo efetivo",
        "plain_text",
        "Leitura segura.",
    )


def test_view_model_builds_request_once_and_maps_original() -> None:
    use_case = _UseCase(_result())

    state = EffectiveApplicationResumeViewModel(use_case).load(7)  # type: ignore[arg-type]

    assert use_case.requests == [7]
    assert state.is_original
    assert state.is_available
    with pytest.raises(FrozenInstanceError):
        state.content = "alterado"  # type: ignore[misc]


def test_view_model_maps_generated_version() -> None:
    state = EffectiveApplicationResumeViewModel(_UseCase(_result(ApplicationResumeSource.RESUME_VERSION))).load(7)  # type: ignore[arg-type]

    assert state.is_generated_version
    assert state.version_label == "Versão v3"


def test_preview_panel_is_read_only_and_clears_state(qapp) -> None:
    panel = EffectiveApplicationResumePreviewPanel()
    state = EffectiveApplicationResumeViewModel(_UseCase(_result())).load(7)  # type: ignore[arg-type]

    panel.render(state)
    assert panel.content.isReadOnly()
    assert panel.content.toPlainText() == "Conteúdo efetivo"
    assert "Currículo original" in panel.source_label.text()

    panel.show_empty_state()
    assert panel.content.toPlainText() == ""
