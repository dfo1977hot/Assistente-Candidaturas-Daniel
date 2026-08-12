from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
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
from acd.services.application_service import ApplicationService
from acd.services.interview_service import InterviewService


class InterviewPage(BasePage):
    """Página de cadastro e gerenciamento de entrevistas."""

    def __init__(
        self, interview_service: InterviewService, application_service: ApplicationService
    ) -> None:
        super().__init__("Entrevistas")

        self.interview_service = interview_service
        self.application_service = application_service
        self.current_interview_id: int | None = None

        self.application_combo = QComboBox()
        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setCalendarPopup(True)
        self.datetime_input.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.type_combo = QComboBox()
        self.interviewer_input = QLineEdit()
        self.interviewer_email_input = QLineEdit()
        self.link_input = QLineEdit()
        self.location_input = QLineEdit()
        self.duration_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(90)
        self.feedback_input = QTextEdit()
        self.feedback_input.setMaximumHeight(90)
        self.result_combo = QComboBox()
        self.search_input = QLineEdit()
        self.filter_type_combo = QComboBox()
        self.filter_result_combo = QComboBox()
        self.filter_button = QPushButton("Filtrar")
        self.save_button = QPushButton("Salvar")
        self.delete_button = QPushButton("Excluir")
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Candidatura", "Tipo", "Data", "Resultado", "Entrevistador"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().hide()
        self.table.setCornerButtonEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().hide()
        self.table.setCornerButtonEnabled(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)

        self._setup_controls()
        self._load_applications()
        self._load_interviews()

    def refresh_reference_data(self) -> None:
        """Atualiza candidaturas e entrevistas ao entrar na página."""
        selected_application = self.application_combo.currentData()
        self._load_applications()
        if selected_application not in (None, ""):
            index = self.application_combo.findData(selected_application)
            if index >= 0:
                self.application_combo.setCurrentIndex(index)
        self._load_interviews()

    def _setup_controls(self) -> None:
        self.type_combo.addItems(
            ["RH", "Gestor", "Técnica", "Painel", "Case", "Teste Prático", "Final"]
        )
        self.result_combo.addItems(
            ["Agendada", "Realizada", "Aprovada", "Reprovada", "Cancelada", "Reagendada"]
        )
        self.filter_type_combo.addItems(
            ["", "RH", "Gestor", "Técnica", "Painel", "Case", "Teste Prático", "Final"]
        )
        self.filter_result_combo.addItems(
            ["", "Agendada", "Realizada", "Aprovada", "Reprovada", "Cancelada", "Reagendada"]
        )


        form_columns = QHBoxLayout()

        first_column = QFormLayout()
        first_column.addRow(QLabel("Candidatura"), self.application_combo)
        first_column.addRow(QLabel("Data e hora"), self.datetime_input)
        first_column.addRow(QLabel("Tipo"), self.type_combo)
        first_column.addRow(QLabel("Resultado"), self.result_combo)

        second_column = QFormLayout()
        second_column.addRow(QLabel("Entrevistador"), self.interviewer_input)
        second_column.addRow(QLabel("E-mail"), self.interviewer_email_input)
        second_column.addRow(QLabel("Duração"), self.duration_input)

        third_column = QFormLayout()
        third_column.addRow(QLabel("Link"), self.link_input)
        third_column.addRow(QLabel("Local"), self.location_input)

        form_columns.addLayout(first_column, 1)
        form_columns.addLayout(second_column, 1)
        form_columns.addLayout(third_column, 1)

        full_width_fields = QFormLayout()
        full_width_fields.addRow(QLabel("Observações"), self.notes_input)
        full_width_fields.addRow(QLabel("Feedback"), self.feedback_input)

        actions = QGridLayout()
        for index, button in enumerate((self.save_button, self.delete_button)):
            actions.addWidget(button, index // 3, index % 3)
        self.save_button.clicked.connect(self._save_interview)
        self.delete_button.clicked.connect(self._delete_interview)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_button)
        self.filter_button.clicked.connect(self._filter_interviews)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Tipo"))
        filter_layout.addWidget(self.filter_type_combo)
        filter_layout.addWidget(QLabel("Resultado"))
        filter_layout.addWidget(self.filter_result_combo)

        self.layout.addLayout(search_layout)
        self.layout.addLayout(filter_layout)
        self.layout.addWidget(self.table)
        self.layout.addLayout(form_columns)
        self.layout.addLayout(full_width_fields)
        self.layout.addLayout(actions)

    def _load_applications(self) -> None:
        applications = self.application_service.list_applications()
        self.application_combo.clear()
        self.application_combo.addItem("", "")
        for application in applications:
            label = f"#{application.id} - {application.company.name if application.company else ''} / {application.job.title if application.job else ''}"
            self.application_combo.addItem(label, application.id)

    def _save_interview(self) -> None:
        try:
            application_id = self.application_combo.currentData()
            interview_date = self.datetime_input.dateTime().toPython()
            interview_type = self.type_combo.currentText()
            interviewer = self.interviewer_input.text().strip()
            interviewer_email = self.interviewer_email_input.text().strip()
            meeting_link = self.link_input.text().strip()
            location = self.location_input.text().strip()
            duration = self.duration_input.text().strip()
            notes = self.notes_input.toPlainText().strip()
            feedback = self.feedback_input.toPlainText().strip()
            result = self.result_combo.currentText()

            if application_id in (None, ""):
                raise ValueError("Selecione uma candidatura.")
            application_id_value = int(application_id)

            if self.current_interview_id is None:
                self.interview_service.create_interview(
                    application_id=application_id_value,
                    interview_date=interview_date,
                    interview_type=interview_type,
                    interviewer=interviewer,
                    interviewer_email=interviewer_email,
                    meeting_link=meeting_link,
                    location=location,
                    duration=duration,
                    notes=notes,
                    feedback=feedback,
                    result=result,
                )
            else:
                self.interview_service.update_interview(
                    self.current_interview_id,
                    application_id=application_id_value,
                    interview_date=interview_date,
                    interview_type=interview_type,
                    interviewer=interviewer,
                    interviewer_email=interviewer_email,
                    meeting_link=meeting_link,
                    location=location,
                    duration=duration,
                    notes=notes,
                    feedback=feedback,
                    result=result,
                )

            self._clear_form()
            self._load_interviews()
        except ValueError as exc:
            QMessageBox.warning(self, "Dados inválidos", str(exc))
        except Exception as exc:  # pragma: no cover - defensive UI handling
            QMessageBox.critical(self, "Erro", str(exc))

    def _delete_interview(self) -> None:
        if self.current_interview_id is None:
            QMessageBox.information(
                self,
                "Entrevista",
                "Selecione uma entrevista para excluir.",
            )
            return
        confirmation = QMessageBox.question(
            self, "Confirmar exclusão", "Deseja excluir esta entrevista?"
        )
        if confirmation != QMessageBox.Yes:
            return
        try:
            deleted = self.interview_service.delete_interview(
                self.current_interview_id
            )
            if not deleted:
                QMessageBox.warning(
                    self,
                    "Entrevista",
                    "A entrevista não pôde ser excluída.",
                )
                return
            self._clear_form()
            self._load_interviews()
        except Exception as exc:
            if not _is_integrity_error(exc):
                QMessageBox.critical(
                    self,
                    "Não foi possível excluir",
                    f"A entrevista possui registros vinculados ou ocorreu um erro:\n{exc}",
                )
                return
            QMessageBox.warning(
                self,
                'Exclus?o bloqueada',
                'Esta entrevista possui registros vinculados. Exclua ou desassocie esses registros antes de tentar novamente.',
            )

    def _on_row_selected(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        self.current_interview_id = int(self.table.item(row, 0).text())
        interview = next(
            (
                item
                for item in self.interview_service.list_interviews()
                if item.id == self.current_interview_id
            ),
            None,
        )
        if interview is None:
            return

        application_index = self.application_combo.findData(interview.application_id)
        if application_index >= 0:
            self.application_combo.setCurrentIndex(application_index)
        self.datetime_input.setDateTime(interview.interview_date)
        self.type_combo.setCurrentText(interview.interview_type or "")
        self.interviewer_input.setText(interview.interviewer or "")
        self.interviewer_email_input.setText(interview.interviewer_email or "")
        self.link_input.setText(interview.meeting_link or "")
        self.location_input.setText(interview.location or "")
        self.duration_input.setText(str(interview.duration or ""))
        self.notes_input.setPlainText(interview.notes or "")
        self.feedback_input.setPlainText(interview.feedback or "")
        self.result_combo.setCurrentText(interview.result or "")

    def _load_interviews(self) -> None:
        interviews = self.interview_service.list_interviews()
        self._render_interviews(interviews)

    def _filter_interviews(self) -> None:
        interview_type = self.filter_type_combo.currentText() or None
        result = self.filter_result_combo.currentText() or None
        query = self.search_input.text().strip()
        if query:
            interviews = self.interview_service.search_interviews(query)
        else:
            interviews = self.interview_service.filter_interviews(
                interview_type=interview_type, result=result
            )
        self._render_interviews(interviews)

    def _render_interviews(self, interviews: list) -> None:
        self.table.setRowCount(len(interviews))
        for row, interview in enumerate(interviews):
            self.table.setItem(row, 0, QTableWidgetItem(str(interview.id)))
            self.table.setItem(row, 1, QTableWidgetItem(f"#{interview.application_id}"))
            self.table.setItem(row, 2, QTableWidgetItem(interview.interview_type))
            self.table.setItem(
                row, 3, QTableWidgetItem(interview.interview_date.strftime("%d/%m/%Y %H:%M"))
            )
            self.table.setItem(row, 4, QTableWidgetItem(interview.result))
            self.table.setItem(row, 5, QTableWidgetItem(interview.interviewer))
        self.table.resizeColumnsToContents()

    def _clear_form(self) -> None:
        self.current_interview_id = None
        self.application_combo.setCurrentIndex(0)
        self.datetime_input.setDateTime(datetime.now())
        self.type_combo.setCurrentIndex(0)
        self.interviewer_input.clear()
        self.interviewer_email_input.clear()
        self.link_input.clear()
        self.location_input.clear()
        self.duration_input.clear()
        self.notes_input.clear()
        self.feedback_input.clear()
        self.result_combo.setCurrentIndex(0)


def _is_integrity_error(exc: BaseException) -> bool:
    current: BaseException | None = exc
    while current is not None:
        if current.__class__.__name__ == "IntegrityError":
            return True
        current = current.__cause__ or current.__context__
    return False
