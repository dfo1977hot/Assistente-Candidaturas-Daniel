"""Passive visual projection for Candidate Decision Support."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.models.candidate_decision_action import CandidateDecisionAction
from acd.presentation.models.candidate_decision_view_state import CandidateDecisionViewState


class CandidateDecisionPanel(QWidget):
    """Render a ``CandidateDecisionViewState`` without applying business rules."""

    action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._empty_message = "Selecione uma candidatura para visualizar a análise."

        layout = QVBoxLayout(self)
        group = QGroupBox("Decisão da candidatura")
        group_layout = QVBoxLayout(group)
        self.empty_state_label = QLabel(self._empty_message)
        self.empty_state_label.setWordWrap(True)
        group_layout.addWidget(self.empty_state_label)

        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        self.headline_label = QLabel()
        self.headline_label.setWordWrap(True)
        details_layout.addWidget(self.headline_label)

        form = QFormLayout()
        self.decision_label = QLabel()
        self.score_label = QLabel()
        self.confidence_label = QLabel()
        form.addRow("Decisão", self.decision_label)
        form.addRow("Score", self.score_label)
        form.addRow("Confiança", self.confidence_label)
        details_layout.addLayout(form)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        details_layout.addWidget(self.summary_label)
        self.reasons_label = self._create_section_label(details_layout, "Motivos")
        self.strengths_label = self._create_section_label(details_layout, "Pontos positivos")
        self.risks_label = self._create_section_label(details_layout, "Pontos de atenção")
        self.gaps_label = self._create_section_label(details_layout, "Lacunas")
        self.recommendations_label = self._create_section_label(details_layout, "Recomendações")

        self.actions_group = QGroupBox("Próximos passos")
        self.actions_layout = QHBoxLayout(self.actions_group)
        self.actions_group.hide()
        details_layout.addWidget(self.actions_group)

        group_layout.addWidget(self.details_widget)
        layout.addWidget(group)
        self.show_empty_state()

    def render(self, state: CandidateDecisionViewState) -> None:
        """Render the values already prepared by the ViewModel."""
        self.empty_state_label.hide()
        self.details_widget.show()
        self.decision_label.setText(state.decision)
        self.score_label.setText("—" if state.score is None else f"{state.score:g}")
        self.confidence_label.setText(state.confidence)
        self.headline_label.setText(state.headline)
        self.summary_label.setText(state.summary)
        self._set_section(self.reasons_label, state.reasons)
        self._set_section(self.strengths_label, state.strengths)
        self._set_section(self.risks_label, state.risks)
        self._set_section(self.gaps_label, state.gaps)
        self._set_section(self.recommendations_label, state.recommendations)

    def show_empty_state(self) -> None:
        """Show the neutral state used when no application is selected."""
        self.details_widget.hide()
        self.empty_state_label.setText(self._empty_message)
        self.empty_state_label.show()

    def render_actions(self, actions: tuple[CandidateDecisionAction, ...]) -> None:
        """Render user-triggered navigation actions supplied by the page."""
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for action in actions:
            button = QPushButton(action.label)
            button.setEnabled(action.enabled)
            button.setToolTip(action.description)
            button.clicked.connect(lambda _checked=False, action_id=action.id: self.action_requested.emit(action_id))
            self.actions_layout.addWidget(button)
        self.actions_group.setVisible(bool(actions))

    @staticmethod
    def _create_section_label(layout: QVBoxLayout, title: str) -> QLabel:
        label = QLabel()
        label.setObjectName(title)
        label.setWordWrap(True)
        layout.addWidget(label)
        return label

    @staticmethod
    def _set_section(label: QLabel, values: tuple[str, ...]) -> None:
        label.setText(
            f"{label.objectName()}\n" + "\n".join(f"• {value}" for value in values)
        )
        label.setVisible(bool(values))
