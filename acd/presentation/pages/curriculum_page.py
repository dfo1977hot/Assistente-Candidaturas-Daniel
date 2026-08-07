from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
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
from acd.services.curriculum_document_service import CurriculumDocumentError
from acd.services.curriculum_service import CurriculumService


class CurriculumPage(BasePage):
    def __init__(self, curriculum_service: CurriculumService) -> None:
        super().__init__("Currículos")
        self.curriculum_service = curriculum_service
        self.current_curriculum_id: int | None = None
        self.pending_file_path: Path | None = None

        self.name_input = QLineEdit()
        self.version_input = QLineEdit()
        self.language_input = QLineEdit()
        self.description_input = QTextEdit()
        self.file_name_label = QLabel("Nenhum arquivo anexado")
        self.file_details_label = QLabel("")
        self.file_integrity_label = QLabel("Sem arquivo")
        self.select_file_button = QPushButton("Selecionar arquivo")
        self.open_file_button = QPushButton("Abrir arquivo")
        self.replace_file_button = QPushButton("Substituir arquivo")
        self.remove_file_button = QPushButton("Remover arquivo")
        self.search_input = QLineEdit()
        self.search_button = QPushButton("Pesquisar")
        self.save_button = QPushButton("Salvar")
        self.duplicate_button = QPushButton("Duplicar")
        self.activate_button = QPushButton("Ativar")
        self.delete_button = QPushButton("Excluir")

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nome", "Versão", "Idioma", "Arquivo", "Padrão"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.table.setCornerButtonEnabled(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)

        self._setup_controls()
        self._set_document_buttons(False)
        self._load_curricula()

    def _setup_controls(self) -> None:
        form = QFormLayout()
        for label, widget in (
            ("Nome", self.name_input), ("Versão", self.version_input),
            ("Idioma", self.language_input), ("Descrição", self.description_input),
            ("Arquivo", self.file_name_label), ("Detalhes", self.file_details_label),
            ("Integridade", self.file_integrity_label),
        ):
            form.addRow(QLabel(label), widget)

        document_actions = QHBoxLayout()
        for button in (
            self.select_file_button, self.open_file_button,
            self.replace_file_button, self.remove_file_button,
        ):
            document_actions.addWidget(button)
        document_actions.addStretch()

        actions = QHBoxLayout()
        for button in (
            self.save_button, self.duplicate_button,
            self.activate_button, self.delete_button,
        ):
            actions.addWidget(button)
        actions.addStretch()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        self.select_file_button.clicked.connect(self._select_file)
        self.replace_file_button.clicked.connect(self._select_file)
        self.open_file_button.clicked.connect(self._open_file)
        self.remove_file_button.clicked.connect(self._remove_file)
        self.save_button.clicked.connect(self._save_curriculum)
        self.duplicate_button.clicked.connect(self._duplicate_curriculum)
        self.activate_button.clicked.connect(self._activate_curriculum)
        self.delete_button.clicked.connect(self._delete_curriculum)
        self.search_button.clicked.connect(self._search_curricula)

        self.layout.addLayout(form)
        self.layout.addLayout(document_actions)
        self.layout.addLayout(actions)
        self.layout.addLayout(search_layout)
        self.layout.addWidget(self.table)

    def _save_curriculum(self) -> None:
        try:
            payload = {
                "name": self.name_input.text().strip(),
                "version": self.version_input.text().strip() or "v1.0",
                "language": self.language_input.text().strip() or "pt-BR",
                "description": self.description_input.toPlainText().strip(),
            }
            if not payload["name"]:
                raise ValueError("Informe o nome do currículo.")
            if self.current_curriculum_id is None:
                saved = self.curriculum_service.create_curriculum(**payload)
                self.current_curriculum_id = saved.id
            else:
                saved = self.curriculum_service.update_curriculum(
                    self.current_curriculum_id, **payload
                )
                if saved is None:
                    raise ValueError("Currículo não encontrado.")
            if self.pending_file_path:
                self.curriculum_service.attach_document(
                    self.current_curriculum_id, self.pending_file_path
                )
            self._clear_form()
            self._load_curricula()
        except (ValueError, CurriculumDocumentError) as exc:
            QMessageBox.warning(self, "Dados inválidos", str(exc))
        except Exception:
            QMessageBox.critical(self, "Erro", "Não foi possível salvar o currículo.")

    def _select_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self, "Selecionar arquivo de currículo", "",
            "Currículos (*.docx *.pdf);;Todos os arquivos (*.*)",
        )
        if not selected:
            return
        path = Path(selected)
        if path.suffix.lower() not in {".docx", ".pdf"}:
            QMessageBox.warning(
                self, "Formato não permitido", "Selecione um arquivo DOCX ou PDF."
            )
            return
        self.pending_file_path = path
        self.file_name_label.setText(path.name)
        self.file_details_label.setText("Arquivo selecionado; clique em Salvar.")
        self.file_integrity_label.setText("Pendente")
        self.select_file_button.setEnabled(False)
        self.replace_file_button.setEnabled(True)

    def _open_file(self) -> None:
        if self.current_curriculum_id is None:
            return
        try:
            self.curriculum_service.open_document(self.current_curriculum_id)
        except CurriculumDocumentError as exc:
            QMessageBox.warning(self, "Arquivo", str(exc))

    def _remove_file(self) -> None:
        if self.current_curriculum_id is None:
            self.pending_file_path = None
            self._show_no_document()
            return
        answer = QMessageBox.question(
            self, "Remover arquivo",
            "Deseja remover o arquivo anexado deste currículo?\n\n"
            "O cadastro do currículo será preservado.",
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.curriculum_service.remove_document(self.current_curriculum_id)
            self._show_no_document()
            self._load_curricula()
        except CurriculumDocumentError as exc:
            QMessageBox.warning(self, "Arquivo", str(exc))

    def _duplicate_curriculum(self) -> None:
        if self.current_curriculum_id is None:
            QMessageBox.information(self, "Currículo", "Selecione um currículo.")
            return
        self.curriculum_service.duplicate_curriculum(self.current_curriculum_id)
        self._clear_form()
        self._load_curricula()

    def _activate_curriculum(self) -> None:
        if self.current_curriculum_id is not None:
            self.curriculum_service.activate_curriculum(self.current_curriculum_id)
            self._load_curricula()

    def _on_row_selected(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        self.current_curriculum_id = int(self.table.item(row, 0).text())
        self.pending_file_path = None
        curriculum = self.curriculum_service.repository.get_by_id(
            self.current_curriculum_id
        )
        if curriculum is None:
            return
        self.name_input.setText(curriculum.name or "")
        self.version_input.setText(curriculum.version or "")
        self.language_input.setText(curriculum.language or "")
        self.description_input.setPlainText(curriculum.description or "")
        self._show_document(curriculum)

    def _show_document(self, curriculum) -> None:
        if not curriculum.file_relative_path:
            self._show_no_document()
            return
        self.file_name_label.setText(curriculum.file_original_name or "Arquivo anexado")
        self.file_details_label.setText(
            f"{(curriculum.file_extension or '').upper().lstrip('.')} — "
            f"{self._format_size(curriculum.file_size_bytes or 0)}"
        )
        integrity = self.curriculum_service.document_service.verify_integrity(curriculum)
        self.file_integrity_label.setText(integrity.message)
        self._set_document_buttons(True)

    def _show_no_document(self) -> None:
        self.file_name_label.setText("Nenhum arquivo anexado")
        self.file_details_label.clear()
        self.file_integrity_label.setText("Sem arquivo")
        self._set_document_buttons(False)

    def _set_document_buttons(self, has_document: bool) -> None:
        self.select_file_button.setEnabled(not has_document)
        self.open_file_button.setEnabled(has_document)
        self.replace_file_button.setEnabled(has_document)
        self.remove_file_button.setEnabled(has_document)

    def _delete_curriculum(self) -> None:
        if self.current_curriculum_id is None:
            QMessageBox.information(
                self, "Currículo", "Selecione um currículo para excluir."
            )
            return
        if QMessageBox.question(
            self, "Confirmar exclusão", "Deseja excluir este currículo?"
        ) != QMessageBox.Yes:
            return
        try:
            if not self.curriculum_service.delete_curriculum(
                self.current_curriculum_id
            ):
                QMessageBox.warning(
                    self, "Currículo", "O currículo não pôde ser excluído."
                )
                return
            self._clear_form()
            self._load_curricula()
        except Exception as exc:
            if not _is_integrity_error(exc):
                QMessageBox.critical(
                    self,
                    "Não foi possível excluir",
                    "Não foi possível concluir a exclusão.",
                )
                return
            cascade_confirmation = QMessageBox.question(
                self,
                "Registros vinculados",
                "Este currículo possui associações com candidaturas e versões vinculadas.\n\n"
                "Deseja excluir também todos os registros vinculados? "
                "Esta operação não poderá ser desfeita.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if cascade_confirmation != QMessageBox.Yes:
                return
            try:
                deleted = self.curriculum_service.delete_curriculum(
                    self.current_curriculum_id,
                    delete_linked=True,
                )
                if not deleted:
                    QMessageBox.warning(
                        self,
                        "Currículo",
                        "O registro não pôde ser excluído.",
                    )
                    return
                self._clear_form()
                self._load_curricula()
            except Exception:
                QMessageBox.critical(
                    self,
                    "Não foi possível excluir",
                    "Não foi possível excluir o registro e seus vínculos.",
                )

    def _load_curricula(self) -> None:
        self._render_curricula(self.curriculum_service.repository.get_all())

    def _search_curricula(self) -> None:
        query = self.search_input.text().strip()
        curricula = (
            self.curriculum_service.search_curricula(query)
            if query else self.curriculum_service.repository.get_all()
        )
        self._render_curricula(curricula)

    def _render_curricula(self, curricula: list) -> None:
        self.table.setRowCount(len(curricula))
        for row, curriculum in enumerate(curricula):
            values = (
                str(curriculum.id), curriculum.name, curriculum.version,
                curriculum.language, curriculum.file_original_name or "—",
                "Sim" if curriculum.is_default else "Não",
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def _clear_form(self) -> None:
        self.current_curriculum_id = None
        self.pending_file_path = None
        self.name_input.clear()
        self.version_input.clear()
        self.language_input.clear()
        self.description_input.clear()
        self.table.clearSelection()
        self._show_no_document()

    @staticmethod
    def _format_size(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"


def _is_integrity_error(exc: BaseException) -> bool:
    current: BaseException | None = exc
    while current is not None:
        if current.__class__.__name__ == "IntegrityError":
            return True
        current = current.__cause__ or current.__context__
    return False
