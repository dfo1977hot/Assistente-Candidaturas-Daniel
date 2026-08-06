"""Qt tests for the passive resume version review panel."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from acd.application.application_resume_source import ApplicationResumeSource
from acd.presentation.models.resume_adoption_view_state import ResumeAdoptionViewState
from acd.presentation.models.resume_version_review_view_state import (
    ResumeVersionItemViewState,
    ResumeVersionReviewViewState,
)
from acd.presentation.resume_version_review_panel import ResumeVersionReviewPanel


def _state() -> ResumeVersionReviewViewState:
    return ResumeVersionReviewViewState(
        status="success",
        title="Versões deste currículo",
        message="",
        application_id=1,
        original_content="Original " * 60,
        versions=(
            ResumeVersionItemViewState(4, "v1"),
            ResumeVersionItemViewState(5, "v2"),
        ),
        selected_version_id=5,
        selected_content="Conteúdo v2",
        explanation="Explicação v2",
    )


def test_panel_renders_read_only_comparison_and_emits_selection(qapp) -> None:
    panel = ResumeVersionReviewPanel()
    selections: list[int] = []
    panel.version_selected.connect(selections.append)

    panel.render(_state())
    panel.version_selector.setCurrentIndex(0)

    assert panel.original_content.isReadOnly()
    assert panel.selected_content.isReadOnly()
    assert panel.original_content.toPlainText().startswith("Original")
    assert panel.selected_content.toPlainText() == "Conteúdo v2"
    assert panel.explanation_label.text() == "Explicação v2"
    assert panel.version_selector.count() == 2
    assert selections == [4]


def test_panel_renders_no_versions_and_clears_previous_content(qapp) -> None:
    panel = ResumeVersionReviewPanel()
    panel.render(_state())
    panel.render(
        ResumeVersionReviewViewState(
            status="no_versions",
            title="Versões deste currículo",
            message="Nenhuma versão gerada para este currículo.",
            application_id=2,
            original_content="Outro original",
        )
    )

    assert panel.version_selector.count() == 0
    assert not panel.details_widget.isVisible()
    assert "Nenhuma versão" in panel.message_label.text()


def test_view_states_are_immutable() -> None:
    state = _state()

    with pytest.raises(FrozenInstanceError):
        state.selected_content = "alterado"  # type: ignore[misc]


def test_panel_distinguishes_visualized_and_adopted_versions_and_emits_only_clicks(qapp) -> None:
    panel = ResumeVersionReviewPanel()
    adopted: list[int] = []
    original: list[bool] = []
    panel.adopt_version_requested.connect(adopted.append)
    panel.use_original_requested.connect(lambda: original.append(True))
    review = _state()
    panel.render(review)
    panel.render_adoption(
        ResumeAdoptionViewState(
            "success", 1, ApplicationResumeSource.RESUME_VERSION, 4, "Atualizado", "ok"
        ),
        review,
    )

    assert "v1" in panel.adopted_source_label.text()
    assert panel.adopt_button.isEnabled()
    assert panel.use_original_button.isEnabled()
    panel.version_selector.setCurrentIndex(0)
    assert adopted == []
    panel.adopt_button.click()
    panel.use_original_button.click()
    assert adopted == [4]
    assert original == [True]


def test_panel_disables_redundant_original_and_adoption_actions(qapp) -> None:
    panel = ResumeVersionReviewPanel()
    review = _state()
    panel.render(review)
    panel.render_adoption(
        ResumeAdoptionViewState(
            "success", 1, ApplicationResumeSource.ORIGINAL, None, "Atualizado", "ok"
        ),
        review,
    )
    assert not panel.use_original_button.isEnabled()
    panel.set_adoption_running(True)
    assert not panel.adopt_button.isEnabled()
