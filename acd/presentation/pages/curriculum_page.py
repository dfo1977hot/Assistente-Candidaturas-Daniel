from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
)

from acd.presentation.pages.base_page import BasePage
from acd.services.curriculum_service import CurriculumService


class CurriculumPage(BasePage):
    """Página de gerenciamento de currículos."""

    def __init__(self, curriculum_service: CurriculumService) -> None:
        super().__init__("Currículos")

        self.curriculum_service = curriculum_service
        self.current_curriculum_id: int | None = None

        self.name_input = QLineEdit()
        self.version_input = QLineEdit()
        self.language_input = QLineEdit()
        self.description_input = QTextEdit()
        self.search_input = QLineEdit()
        self.search_button = QPushButton("Pesquisar")
        self.save_button = QPushButton("Salvar")
        self.duplicate_button = QPushButton("Duplicar")
        self.activate_button = QPushButton("Ativar")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Versão", "Idioma", "Padrão"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)

        self._setup_controls()
        self._load_curricula()

    def _setup_controls(self) -> None:
        form = QFormLayout()
        form.addRow(QLabel("Nome"), self.name_input)
        form.addRow(QLabel("Versão"), self.version_input)
        form.addRow(QLabel("Idioma"), self.language_input)
        form.addRow(QLabel("Descrição"), self.description_input)

        actions = QHBoxLayout()
        actions.addWidget(self.save_button)
        actions.addWidget(self.duplicate_button)
        actions.addWidget(self.activate_button)
        actions.addStretch()
        self.save_button.clicked.connect(self._save_curriculum)
        self.duplicate_button.clicked.connect(self._duplicate_curriculum)
        self.activate_button.clicked.connect(self._activate_curriculum)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        self.search_button.clicked.connect(self._search_curricula)

        self.layout.addLayout(form)
        self.layout.addLayout(actions)
        self.layout.addLayout(search_layout)
        self.layout.addWidget(self.table)

    def _save_curriculum(self) -> None:
        try:
            self.curriculum_service.create_curriculum(
                name=self.name_input.text().strip(),
                version=self.version_input.text().strip() or "v1.0",
                language=self.language_input.text().strip() or "pt-BR",
                description=self.description_input.toPlainText().strip(),
            )
            self._clear_form()
            self._load_curricula()
        except ValueError as exc:
            QMessageBox.warning(self, "Dados inválidos", str(exc))

    def _duplicate_curriculum(self) -> None:
        if self.current_curriculum_id is None:
            return
        self.curriculum_service.duplicate_curriculum(self.current_curriculum_id)
        self._load_curricula()

    def _activate_curriculum(self) -> None:
        if self.current_curriculum_id is None:
            return
        self.curriculum_service.activate_curriculum(self.current_curriculum_id)
        self._load_curricula()

    def _on_row_selected(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        self.current_curriculum_id = int(self.table.item(row, 0).text())

    def _load_curricula(self) -> None:
        curricula = self.curriculum_service.repository.get_all()
        self._render_curricula(curricula)

    def _search_curricula(self) -> None:
        query = self.search_input.text().strip()
        curricula = (
            self.curriculum_service.search_curricula(query)
            if query
            else self.curriculum_service.repository.get_all()
        )
        self._render_curricula(curricula)

    def _render_curricula(self, curricula: list) -> None:
        self.table.setRowCount(len(curricula))
        for row, curriculum in enumerate(curricula):
            self.table.setItem(row, 0, QTableWidgetItem(str(curriculum.id)))
            self.table.setItem(row, 1, QTableWidgetItem(curriculum.name))
            self.table.setItem(row, 2, QTableWidgetItem(curriculum.version))
            self.table.setItem(row, 3, QTableWidgetItem(curriculum.language))
            self.table.setItem(row, 4, QTableWidgetItem("Sim" if curriculum.is_default else "Não"))
        self.table.resizeColumnsToContents()

    def _clear_form(self) -> None:
        self.current_curriculum_id = None
        self.name_input.clear()
        self.version_input.clear()
        self.language_input.clear()
        self.description_input.clear()
