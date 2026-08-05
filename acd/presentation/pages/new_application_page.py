from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.pages.new_application_view_model import (
    NewApplicationViewModel,
)


class NewApplicationPage(QWidget):
    """
    Tela responsável por iniciar uma nova candidatura.
    """

    def __init__(
        self,
        view_model: NewApplicationViewModel | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._view_model = (
            view_model
            if view_model is not None
            else NewApplicationViewModel()
        )

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Nova Candidatura")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)

        form = QFormLayout()

        self.company_edit = QLineEdit()
        self.job_edit = QLineEdit()
        self.description_edit = QTextEdit()

        form.addRow("Empresa", self.company_edit)
        form.addRow("Cargo", self.job_edit)
        form.addRow("Descrição", self.description_edit)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        self.start_button = QPushButton("Iniciar candidatura")
        self.clear_button = QPushButton("Limpar")

        buttons.addWidget(self.start_button)
        buttons.addWidget(self.clear_button)

        layout.addLayout(buttons)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.start_button.clicked.connect(self._start_application)
        self.clear_button.clicked.connect(self._clear)

    def _start_application(self) -> None:
        snapshot = self._view_model.start_application(
            company_name=self.company_edit.text(),
            job_title=self.job_edit.text(),
            job_description=self.description_edit.toPlainText(),
        )

        self.status_label.setText(
            f"Candidatura iniciada para {snapshot.company_name}"
        )

    def _clear(self) -> None:
        self.company_edit.clear()
        self.job_edit.clear()
        self.description_edit.clear()

        self._view_model.clear()

        self.status_label.clear()