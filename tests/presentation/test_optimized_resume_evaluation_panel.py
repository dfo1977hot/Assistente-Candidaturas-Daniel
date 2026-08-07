"""Qt tests for explicit transient resume version evaluations."""

from __future__ import annotations

from acd.presentation.models.optimized_resume_evaluation_view_state import (
    OptimizedResumeEvaluationViewState,
)
from acd.presentation.models.resume_version_review_view_state import (
    ResumeVersionItemViewState,
    ResumeVersionReviewViewState,
)
from acd.presentation.resume_version_review_panel import ResumeVersionReviewPanel


def _review_state() -> ResumeVersionReviewViewState:
    return ResumeVersionReviewViewState(
        status="success",
        title="Versões deste currículo",
        message="",
        application_id=3,
        versions=(ResumeVersionItemViewState(8, "v2"),),
        selected_version_id=8,
        selected_content="Conteúdo otimizado",
    )


def test_explicit_button_is_enabled_only_for_a_selected_version(qapp) -> None:
    panel = ResumeVersionReviewPanel()
    requested: list[int] = []
    panel.evaluation_requested.connect(requested.append)
    panel.set_evaluation_available(True)

    assert not panel.evaluate_button.isEnabled()
    panel.render(_review_state())

    assert panel.evaluate_button.text() == "Avaliar versão otimizada"
    assert panel.evaluate_button.isEnabled()
    assert requested == []

    panel.evaluate_button.click()

    assert requested == [8]
    panel.set_evaluation_running(True)
    assert not panel.evaluate_button.isEnabled()


def test_panel_renders_transient_result_and_clears_it_on_version_change(qapp) -> None:
    panel = ResumeVersionReviewPanel()
    panel.set_evaluation_available(True)
    panel.render(_review_state())
    panel.render_evaluation(
        OptimizedResumeEvaluationViewState(
            status="success",
            title="Avaliação atual da versão selecionada",
            message="Este resultado não foi salvo no histórico.",
            application_id=3,
            resume_version_id=8,
            original_score=55.0,
            optimized_score=70.0,
            score_delta=15.0,
            persisted=False,
        )
    )

    assert "ATS original: 55.0" in panel.evaluation_label.text()
    assert "não foi salvo" in panel.evaluation_label.text()

    panel._emit_selected_version(0)

    assert panel.evaluation_label.text() == ""
