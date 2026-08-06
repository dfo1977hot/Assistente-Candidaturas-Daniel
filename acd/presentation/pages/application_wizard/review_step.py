from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from acd.presentation.pages.base_page import BasePage
from acd.presentation.pages.new_application_view_model import (
    NewApplicationViewModel,
)


class ReviewStep(BasePage):
    """
    Última etapa antes do processamento da candidatura.
    """

    completed = Signal()

    def __init__(
        self,
        view_model: NewApplicationViewModel,
    ) -> None:
        super().__init__()

        self._view_model = view_model

        self._build_ui()

    def on_enter(self) -> None:
        state = self._view_model.state

        text = (
            f"Empresa:\n"
            f"{state.company_name}\n\n"
            f"Cargo:\n"
            f"{state.job_title}\n\n"
            f"URL:\n"
            f"{state.job_url}\n\n"
            f"Descrição:\n"
            f"{state.job_description}"
        )

        self._summary.setPlainText(text)

    def validate_page(self) -> bool:
        return True

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("Revise os dados da candidatura")
        )

        self._summary = QTextEdit()
        self._summary.setReadOnly(True)

        layout.addWidget(self._summary)

        self._finish_button = QPushButton(
            "Iniciar candidatura"
        )

        self._finish_button.clicked.connect(
            self.completed.emit
        )

        layout.addWidget(self._finish_button)