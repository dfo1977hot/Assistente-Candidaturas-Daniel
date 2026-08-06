"""Passive read-only preview for an application's effective resume."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QTextEdit, QVBoxLayout, QWidget

from acd.presentation.models.effective_application_resume_view_state import (
    EffectiveApplicationResumeViewState,
)


class EffectiveApplicationResumePreviewPanel(QWidget):
    """Render supplied preview state without accessing application dependencies."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        group = QGroupBox("Currículo efetivamente usado nesta candidatura")
        group_layout = QVBoxLayout(group)
        self.source_label = QLabel()
        self.source_label.setWordWrap(True)
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        self.content.setMinimumHeight(180)
        group_layout.addWidget(self.source_label)
        group_layout.addWidget(self.message_label)
        group_layout.addWidget(self.content)
        layout.addWidget(group)
        self.show_empty_state()

    def render(self, state: EffectiveApplicationResumeViewState) -> None:
        """Render one immutable state projection."""
        self.source_label.setText(f"Fonte: {state.source_label}")
        self.message_label.setText(state.message)
        self.message_label.setVisible(bool(state.message))
        self.content.setPlainText(state.content)

    def show_empty_state(self) -> None:
        """Remove data belonging to a previously selected application."""
        self.source_label.setText("Fonte: indisponível")
        self.message_label.setText("Selecione uma candidatura para visualizar o currículo efetivo.")
        self.message_label.show()
        self.content.clear()
