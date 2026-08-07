"""Qt tests for the passive Candidate Decision panel."""

from __future__ import annotations

import pytest

from acd.presentation.candidate_decision_panel import CandidateDecisionPanel
from acd.presentation.models.candidate_decision_action import CandidateDecisionAction
from acd.presentation.models.candidate_decision_view_state import CandidateDecisionViewState


@pytest.fixture
def decision_state() -> CandidateDecisionViewState:
    """Provide a complete UI state without invoking Application logic."""
    return CandidateDecisionViewState(
        decision="STRONG_APPLY",
        score=87.0,
        confidence="HIGH",
        headline="Strong application",
        summary="The application has strong persisted evidence.",
        reasons=("Evidence is consistent",),
        strengths=("Relevant experience",),
        risks=("Limited interview evidence",),
        gaps=("Cloud certification",),
        recommendations=("Apply now",),
    )


def test_candidate_decision_panel_renders_view_state(qapp, decision_state) -> None:
    """The panel displays all values supplied by the immutable UI contract."""
    panel = CandidateDecisionPanel()

    panel.render(decision_state)

    assert panel.decision_label.text() == "STRONG_APPLY"
    assert panel.score_label.text() == "87"
    assert panel.confidence_label.text() == "HIGH"
    assert panel.headline_label.text() == "Strong application"
    assert panel.summary_label.text() == "The application has strong persisted evidence."
    assert "Evidence is consistent" in panel.reasons_label.text()
    assert "Relevant experience" in panel.strengths_label.text()
    assert "Limited interview evidence" in panel.risks_label.text()
    assert "Cloud certification" in panel.gaps_label.text()
    assert "Apply now" in panel.recommendations_label.text()


def test_candidate_decision_panel_handles_optional_fields_and_unknown_state(qapp) -> None:
    """Unknown decisions and unavailable optional data remain neutral UI content."""
    panel = CandidateDecisionPanel()
    state = CandidateDecisionViewState(
        decision="FUTURE_STATE",
        score=None,
        confidence="UNKNOWN",
        headline="Future decision",
        summary="A future state is displayed without interpretation.",
        reasons=(),
        strengths=(),
        risks=(),
        gaps=(),
        recommendations=(),
    )

    panel.render(state)

    assert panel.decision_label.text() == "FUTURE_STATE"
    assert panel.score_label.text() == "—"
    assert not panel.reasons_label.isVisible()
    assert not panel.recommendations_label.isVisible()


def test_candidate_decision_panel_renders_insufficient_data_as_valid_state(qapp) -> None:
    """INSUFFICIENT_DATA is displayed as supplied rather than treated as an error."""
    panel = CandidateDecisionPanel()
    state = CandidateDecisionViewState(
        decision="INSUFFICIENT_DATA",
        score=None,
        confidence="LOW",
        headline="Insufficient data",
        summary="More persisted evidence is required for a decision.",
        reasons=(),
        strengths=(),
        risks=(),
        gaps=(),
        recommendations=(),
    )

    panel.render(state)

    assert panel.decision_label.text() == "INSUFFICIENT_DATA"
    assert panel.summary_label.text() == "More persisted evidence is required for a decision."


def test_candidate_decision_panel_shows_empty_state(qapp) -> None:
    """No selection is represented without invoking decision logic."""
    panel = CandidateDecisionPanel()

    panel.show_empty_state()

    assert not panel.empty_state_label.isHidden()
    assert "Selecione uma candidatura" in panel.empty_state_label.text()


def test_candidate_decision_panel_emits_action_only_after_click(qapp) -> None:
    panel = CandidateDecisionPanel()
    requested: list[str] = []
    panel.action_requested.connect(requested.append)

    panel.render_actions((CandidateDecisionAction("review_gaps", "Revisar gaps", "Abrir lacunas.", True),))
    button = panel.actions_layout.itemAt(0).widget()
    assert button is not None

    button.click()

    assert requested == ["review_gaps"]
