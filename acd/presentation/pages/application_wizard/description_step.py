from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from acd.presentation.pages.base_page import BasePage


class DescriptionStep(BasePage):
    """
    Etapa responsável pela captura da descrição da vaga.
    """

    completed = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._build_ui()

    @property
    def description(self) -> str:
        return self._description.toPlainText().strip()

    def validate_page(self) -> bool:
        return bool(self.description)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Descrição da vaga")

        self._description = QPlainTextEdit()

        self._description.setPlaceholderText(
            "Cole aqui a descrição completa da vaga..."
        )

        self._next_button = QPushButton("Próximo")

        self._next_button.clicked.connect(
            self._emit_completed
        )

        layout.addWidget(title)
        layout.addWidget(self._description)
        layout.addWidget(self._next_button)

    def _emit_completed(self) -> None:
        if not self.validate_page():
            return

        self.completed.emit(
            self.description
        )