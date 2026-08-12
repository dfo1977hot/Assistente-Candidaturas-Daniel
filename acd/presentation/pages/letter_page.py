from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
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
from acd.services.cover_letter_service import CoverLetterService
from acd.services.curriculum_service import CurriculumService
from acd.services.job_service import JobService


class LetterPage(BasePage):
    """Gerenciamento, geração, versionamento e exportação de cartas."""

    def __init__(
        self,
        letter_service: CoverLetterService,
        job_service: JobService,
        curriculum_service: CurriculumService,
    ) -> None:
        super().__init__("Cartas")

        self.letter_service = letter_service
        self.job_service = job_service
        self.curriculum_service = curriculum_service
        self.current_letter_id: int | None = None

        self.search_input = QLineEdit()
        self.search_button = QPushButton("Filtrar")
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Empresa", "Cargo", "Tipo", "Idioma", "Versão", "Status", "Data"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)

        self.job_combo = QComboBox()
        self.company_input = QLineEdit()
        self.company_input.setReadOnly(True)
        self.title_input = QLineEdit()
        self.title_input.setReadOnly(True)
        self.recruiter_input = QLineEdit()
        self.recruiter_input.setReadOnly(True)
        self.recruiter_email_input = QLineEdit()
        self.recruiter_email_input.setReadOnly(True)
        self.curriculum_combo = QComboBox()
        self.type_combo = QComboBox()
        self.language_combo = QComboBox()
        self.tone_combo = QComboBox()
        self.length_combo = QComboBox()
        self.version_input = QLineEdit()
        self.version_input.setReadOnly(True)
        self.status_combo = QComboBox()
        self.subject_input = QLineEdit()
        self.content_input = QTextEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(70)

        self.save_button = QPushButton("Salvar")
        self.delete_button = QPushButton("Excluir")
        self.generate_button = QPushButton("Gerar com IA")
        self.copy_button = QPushButton("Copiar")
        self.docx_button = QPushButton("Exportar DOCX")
        self.pdf_button = QPushButton("Exportar PDF")

        self._setup()
        self.refresh_reference_data()
        self._load_letters()

    def _setup(self) -> None:
        self.type_combo.addItems(CoverLetterService.LETTER_TYPES)
        self.language_combo.addItems(CoverLetterService.LANGUAGES)
        self.tone_combo.addItems(CoverLetterService.TONES)
        self.length_combo.addItems(CoverLetterService.LENGTHS)
        self.status_combo.addItems(CoverLetterService.STATUSES)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        columns = QHBoxLayout()
        left = QFormLayout()
        left.addRow(QLabel("Vaga"), self.job_combo)
        left.addRow(QLabel("Empresa"), self.company_input)
        left.addRow(QLabel("Cargo"), self.title_input)
        left.addRow(QLabel("Recrutador"), self.recruiter_input)
        left.addRow(QLabel("E-mail"), self.recruiter_email_input)

        middle = QFormLayout()
        middle.addRow(QLabel("Currículo"), self.curriculum_combo)
        middle.addRow(QLabel("Tipo"), self.type_combo)
        middle.addRow(QLabel("Idioma"), self.language_combo)
        middle.addRow(QLabel("Tom"), self.tone_combo)
        middle.addRow(QLabel("Tamanho"), self.length_combo)

        right = QFormLayout()
        right.addRow(QLabel("Versão"), self.version_input)
        right.addRow(QLabel("Status"), self.status_combo)

        columns.addLayout(left, 1)
        columns.addLayout(middle, 1)
        columns.addLayout(right, 1)

        long_fields = QFormLayout()
        long_fields.addRow(QLabel("Assunto"), self.subject_input)
        long_fields.addRow(QLabel("Carta"), self.content_input)
        long_fields.addRow(QLabel("Observações"), self.notes_input)

        actions = QGridLayout()
        for index, button in enumerate(
            (
                self.save_button,
                self.delete_button,
                self.generate_button,
                self.copy_button,
                self.docx_button,
                self.pdf_button,
            )
        ):
            actions.addWidget(button, 0, index)

        self.layout.addLayout(search_layout)
        self.layout.addWidget(self.table)
        self.layout.addLayout(columns)
        self.layout.addLayout(long_fields)
        self.layout.addLayout(actions)

        self.search_button.clicked.connect(self._filter)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.job_combo.currentIndexChanged.connect(self._on_job_changed)
        self.curriculum_combo.currentIndexChanged.connect(self._update_next_version)
        self.save_button.clicked.connect(self._save)
        self.delete_button.clicked.connect(self._delete)
        self.generate_button.clicked.connect(self._generate)
        self.copy_button.clicked.connect(self._copy)
        self.docx_button.clicked.connect(self._export_docx)
        self.pdf_button.clicked.connect(self._export_pdf)

    def refresh_reference_data(self) -> None:
        selected_job = self.job_combo.currentData()
        selected_curriculum = self.curriculum_combo.currentData()

        self.job_combo.blockSignals(True)
        self.job_combo.clear()
        self.job_combo.addItem("", None)
        for job in self.job_service.list_jobs():
            company = getattr(job.company, "name", "") or ""
            self.job_combo.addItem(f"{company} — {job.title}", job.id)
        self.job_combo.blockSignals(False)

        self.curriculum_combo.blockSignals(True)
        self.curriculum_combo.clear()
        self.curriculum_combo.addItem("", None)
        for curriculum in self.curriculum_service.list_curricula():
            self.curriculum_combo.addItem(
                f"{curriculum.name} — {curriculum.version}",
                curriculum.id,
            )
        self.curriculum_combo.blockSignals(False)

        self._restore_combo(self.job_combo, selected_job)
        self._restore_combo(self.curriculum_combo, selected_curriculum)
        self._on_job_changed()
        self._update_next_version()

    @staticmethod
    def _restore_combo(combo: QComboBox, value: object) -> None:
        if value is None:
            return
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _load_letters(self, rows: list[object] | None = None) -> None:
        letters = rows if rows is not None else self.letter_service.list_letters()
        self.table.setRowCount(len(letters))
        for row, letter in enumerate(letters):
            job = (
                self.job_service.get_job(letter.job_id)
                if letter.job_id is not None
                else None
            )
            company = getattr(getattr(job, "company", None), "name", "") or ""
            cargo = getattr(job, "title", "") or ""
            created = getattr(letter, "created_at", None)
            values = (
                letter.id,
                company,
                cargo,
                letter.letter_type,
                letter.language,
                letter.version,
                letter.status,
                created.strftime("%d/%m/%Y") if created else "",
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))

    def _filter(self) -> None:
        self._load_letters(
            self.letter_service.search_letters(self.search_input.text())
        )

    def _on_row_selected(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        item = self.table.item(rows[0].row(), 0)
        if item is None:
            return
        letter = self.letter_service.get_letter(int(item.text()))
        if letter is None:
            return

        self.current_letter_id = letter.id
        self._set_combo_data(self.job_combo, letter.job_id)
        self._set_combo_data(self.curriculum_combo, letter.curriculum_id)
        self.type_combo.setCurrentText(letter.letter_type)
        self.language_combo.setCurrentText(letter.language)
        self.tone_combo.setCurrentText(letter.tone)
        self.length_combo.setCurrentText(letter.length)
        self.version_input.setText(letter.version)
        self.status_combo.setCurrentText(letter.status)
        self.subject_input.setText(letter.subject)
        self.content_input.setPlainText(letter.content)
        self.notes_input.setPlainText(letter.notes)
        self._on_job_changed()

    @staticmethod
    def _set_combo_data(combo: QComboBox, value: object) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _on_job_changed(self) -> None:
        job_id = self.job_combo.currentData()
        job = self.job_service.get_job(int(job_id)) if job_id else None
        if job is None:
            self.company_input.clear()
            self.title_input.clear()
            self.recruiter_input.clear()
            self.recruiter_email_input.clear()
            return
        self.company_input.setText(getattr(job.company, "name", "") or "")
        self.title_input.setText(job.title)
        self.recruiter_input.setText(job.recruiter or "")
        self.recruiter_email_input.setText(job.recruiter_email or "")
        self._update_next_version()

    def _update_next_version(self) -> None:
        if self.current_letter_id is not None:
            return
        job_id = self.job_combo.currentData()
        curriculum_id = self.curriculum_combo.currentData()
        if not job_id or not curriculum_id:
            self.version_input.setText("V1.0")
            return
        self.version_input.setText(
            self.letter_service.next_version(
                job_id=int(job_id),
                curriculum_id=int(curriculum_id),
            )
        )

    def _save(self) -> None:
        try:
            saved = self.letter_service.save_letter(
                letter_id=self.current_letter_id,
                job_id=int(self.job_combo.currentData() or 0),
                curriculum_id=int(self.curriculum_combo.currentData() or 0),
                version=self.version_input.text(),
                letter_type=self.type_combo.currentText(),
                language=self.language_combo.currentText(),
                tone=self.tone_combo.currentText(),
                length=self.length_combo.currentText(),
                subject=self.subject_input.text(),
                status=self.status_combo.currentText(),
                content=self.content_input.toPlainText(),
                notes=self.notes_input.toPlainText(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Salvar carta", str(exc))
            return
        self.current_letter_id = saved.id
        self._load_letters()
        self._select_row(saved.id)
        QMessageBox.information(self, "Carta", "O registro foi salvo")

    def _generate(self) -> None:
        job_id = int(self.job_combo.currentData() or 0)
        curriculum_id = int(self.curriculum_combo.currentData() or 0)
        if not job_id or not curriculum_id:
            QMessageBox.warning(
                self,
                "Gerar carta",
                "Selecione a vaga e o currículo antes de gerar.",
            )
            return
        try:
            generated = self.letter_service.generate_letter(
                job_id=job_id,
                curriculum_id=curriculum_id,
                letter_type=self.type_combo.currentText(),
                language=self.language_combo.currentText(),
                tone=self.tone_combo.currentText(),
                length=self.length_combo.currentText(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Gerar carta", str(exc))
            return

        self.current_letter_id = generated.id
        self._load_letters()
        self._select_row(generated.id)
        self._on_row_selected()

    def _delete(self) -> None:
        if self.current_letter_id is None:
            return
        answer = QMessageBox.question(
            self,
            "Excluir carta",
            "Deseja excluir esta versão da carta?",
        )
        if answer != QMessageBox.Yes:
            return
        self.letter_service.delete_letter(self.current_letter_id)
        self._clear()
        self._load_letters()

    def _copy(self) -> None:
        text = self.content_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Copiar", "Não há conteúdo para copiar.")
            return
        QGuiApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiar", "Carta copiada para a área de transferência.")

    def _export_docx(self) -> None:
        self._export("docx")

    def _export_pdf(self) -> None:
        self._export("pdf")

    def _export(self, file_type: str) -> None:
        if self.current_letter_id is None:
            QMessageBox.warning(self, "Exportar", "Salve a carta antes de exportar.")
            return
        extension = f".{file_type}"
        default_name = (
            f"carta_{self.company_input.text()}_{self.title_input.text()}_"
            f"{self.version_input.text()}{extension}"
        )
        default_name = "".join(
            character if character.isalnum() or character in "._-" else "_"
            for character in default_name
        )
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar carta",
            str(Path.home() / "Documents" / default_name),
            f"{file_type.upper()} (*{extension})",
        )
        if not path:
            return
        try:
            if file_type == "docx":
                saved = self.letter_service.export_docx(
                    self.current_letter_id,
                    path,
                )
            else:
                saved = self.letter_service.export_pdf(
                    self.current_letter_id,
                    path,
                )
        except Exception as exc:
            QMessageBox.warning(self, "Exportar", str(exc))
            return
        QMessageBox.information(self, "Exportar", f"Arquivo salvo em:\n{saved}")

    def _select_row(self, letter_id: int) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None and item.text() == str(letter_id):
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                return

    def _clear(self) -> None:
        self.current_letter_id = None
        self.subject_input.clear()
        self.content_input.clear()
        self.notes_input.clear()
        self.status_combo.setCurrentText("Rascunho")
        self._update_next_version()

    def on_enter(self) -> None:
        self.refresh_reference_data()
        self._load_letters()
