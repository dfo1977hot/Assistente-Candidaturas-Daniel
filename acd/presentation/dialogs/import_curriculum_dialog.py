from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton


class ImportCurriculumDialog(QDialog):
    """Diálogo simples para importar currículos."""

    def __init__(self) -> None:
        super().__init__()
        self.file_path_input = QLineEdit()
        self.import_button = QPushButton("Importar")
        layout = QFormLayout(self)
        layout.addRow("Arquivo", self.file_path_input)
        layout.addWidget(self.import_button)
