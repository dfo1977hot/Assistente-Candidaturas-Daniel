from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
)

from acd.presentation.pages.base_page import BasePage


class JobStep(BasePage):
    """
    Página responsável por capturar as informações da vaga.
    """

    completed = Signal(str, str)

    def __init__(self) -> None:
        super().__init__("Informações da vaga")

        self.job_title = QLineEdit()
        self.job_title.setPlaceholderText(
            "Cargo"
        )

        self.job_url = QLineEdit()
        self.job_url.setPlaceholderText(
            "Link da vaga (opcional)"
        )

        self.next_button = QPushButton("Continuar")

        self.layout.addWidget(QLabel("Cargo"))

        self.layout.addWidget(self.job_title)

        self.layout.addWidget(QLabel("Link"))

        self.layout.addWidget(self.job_url)

        self.layout.addWidget(self.next_button)

        self.next_button.clicked.connect(
            self._finish
        )

    def _finish(self) -> None:
        self.completed.emit(
            self.job_title.text().strip(),
            self.job_url.text().strip(),
        )

    def validate_page(self) -> bool:
        return bool(
            self.job_title.text().strip()
        )