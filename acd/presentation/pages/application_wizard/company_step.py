from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CompanyStep(QWidget):
    """
    Primeira etapa do Wizard.

    Não conhece o ViewModel.
    Não conhece ApplicationState.
    Apenas coleta dados.
    """

    completed = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.company_edit = QLineEdit()

        self.next_button = QPushButton("Próximo")

        form = QFormLayout()

        form.addRow("Empresa", self.company_edit)

        layout = QVBoxLayout(self)

        layout.addLayout(form)

        layout.addStretch()

        layout.addWidget(self.next_button)

        self.next_button.clicked.connect(
            self._on_next_clicked
        )

    def company_name(self) -> str:
        """
        Retorna o valor informado.
        """
        return self.company_edit.text().strip()

    def _on_next_clicked(self) -> None:
        self.completed.emit(
            self.company_name()
        )