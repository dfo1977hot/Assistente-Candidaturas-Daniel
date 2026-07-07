from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
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
from acd.services.application_service import ApplicationService
from acd.services.company_service import CompanyService
from acd.services.job_service import JobService


class ApplicationPage(BasePage):
    """Página de cadastro e gerenciamento de candidaturas."""

    def __init__(self) -> None:
        super().__init__("Candidaturas")

        self.application_service = ApplicationService()
        self.company_service = CompanyService()
        self.job_service = JobService()
        self.current_application_id: int | None = None

        self.company_combo = QComboBox()
        self.job_combo = QComboBox()
        self.status_combo = QComboBox()
        self.application_date_input = QDateEdit()
        self.next_follow_up_input = QDateEdit()
        self.response_date_input = QDateEdit()
        self.interview_date_input = QDateEdit()
        self.salary_expected_input = QLineEdit()
        self.salary_offered_input = QLineEdit()
        self.channel_input = QLineEdit()
        self.recruiter_name_input = QLineEdit()
        self.recruiter_email_input = QLineEdit()
        self.recruiter_phone_input = QLineEdit()
        self.feedback_input = QTextEdit()
        self.notes_input = QTextEdit()
        self.search_input = QLineEdit()
        self.filter_status_combo = QComboBox()
        self.filter_company_combo = QComboBox()
        self.filter_button = QPushButton("Filtrar")
        self.save_button = QPushButton("Salvar")
        self.delete_button = QPushButton("Excluir")
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Empresa", "Vaga", "Status", "Aplicação", "Follow-up"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)

        self._setup_controls()
        self._load_companies()
        self._load_applications()

    def _setup_controls(self) -> None:
        self.status_combo.addItems(
            [
                "Rascunho",
                "Preparando Currículo",
                "Preparando Carta",
                "Pronta para Aplicação",
                "Aplicada",
                "Em Triagem",
                "Entrevista RH",
                "Teste",
                "Entrevista Técnica",
                "Entrevista Gestor",
                "Oferta",
                "Contratada",
                "Rejeitada",
                "Encerrada",
            ]
        )
        self.filter_status_combo.addItem("", "")
        for index in range(self.status_combo.count()):
            self.filter_status_combo.addItem(self.status_combo.itemText(index))
        self.filter_company_combo.addItem("", "")

        form = QFormLayout()
        form.addRow(QLabel("Empresa"), self.company_combo)
        form.addRow(QLabel("Vaga"), self.job_combo)
        form.addRow(QLabel("Status"), self.status_combo)
        form.addRow(QLabel("Data aplicação"), self.application_date_input)
        form.addRow(QLabel("Próximo follow-up"), self.next_follow_up_input)
        form.addRow(QLabel("Data resposta"), self.response_date_input)
        form.addRow(QLabel("Data entrevista"), self.interview_date_input)
        form.addRow(QLabel("Salário esperado"), self.salary_expected_input)
        form.addRow(QLabel("Salário oferecido"), self.salary_offered_input)
        form.addRow(QLabel("Canal"), self.channel_input)
        form.addRow(QLabel("Recrutador"), self.recruiter_name_input)
        form.addRow(QLabel("E-mail"), self.recruiter_email_input)
        form.addRow(QLabel("Telefone"), self.recruiter_phone_input)
        form.addRow(QLabel("Feedback"), self.feedback_input)
        form.addRow(QLabel("Observações"), self.notes_input)

        actions = QHBoxLayout()
        actions.addWidget(self.save_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        self.save_button.clicked.connect(self._save_application)
        self.delete_button.clicked.connect(self._delete_application)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_button)
        self.filter_button.clicked.connect(self._filter_applications)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self.filter_status_combo)
        filter_layout.addWidget(QLabel("Empresa"))
        filter_layout.addWidget(self.filter_company_combo)

        self.layout.addLayout(form)
        self.layout.addLayout(actions)
        self.layout.addLayout(search_layout)
        self.layout.addLayout(filter_layout)
        self.layout.addWidget(self.table)

    def _load_companies(self) -> None:
        companies = self.company_service.list_companies()
        self.company_combo.clear()
        self.company_combo.addItem("", "")
        self.filter_company_combo.clear()
        self.filter_company_combo.addItem("", "")
        for company in companies:
            self.company_combo.addItem(company.name, company.id)
            self.filter_company_combo.addItem(company.name, company.id)

    def _load_jobs(self) -> None:
        company_id = self.company_combo.currentData()
        self.job_combo.clear()
        self.job_combo.addItem("", "")
        if company_id:
            jobs = self.job_service.filter_jobs(company_id=int(company_id))
            for job in jobs:
                self.job_combo.addItem(job.title, job.id)

    def _save_application(self) -> None:
        try:
            company_id = self.company_combo.currentData()
            job_id = self.job_combo.currentData()
            status = self.status_combo.currentText()
            application_date = (
                self.application_date_input.date().toString("yyyy-MM-dd")
                if self.application_date_input.date().isValid()
                else ""
            )
            next_follow_up = (
                self.next_follow_up_input.date().toString("yyyy-MM-dd")
                if self.next_follow_up_input.date().isValid()
                else ""
            )
            response_date = (
                self.response_date_input.date().toString("yyyy-MM-dd")
                if self.response_date_input.date().isValid()
                else ""
            )
            interview_date = (
                self.interview_date_input.date().toString("yyyy-MM-dd")
                if self.interview_date_input.date().isValid()
                else ""
            )
            salary_expected = self._parse_optional_number(self.salary_expected_input.text())
            salary_offered = self._parse_optional_number(self.salary_offered_input.text())
            channel = self.channel_input.text().strip()
            recruiter_name = self.recruiter_name_input.text().strip()
            recruiter_email = self.recruiter_email_input.text().strip()
            recruiter_phone = self.recruiter_phone_input.text().strip()
            feedback = self.feedback_input.toPlainText().strip()
            notes = self.notes_input.toPlainText().strip()

            if self.current_application_id is None:
                self.application_service.create_application(
                    job_id=int(job_id),
                    company_id=int(company_id),
                    status=status,
                    application_date=application_date,
                    next_follow_up=next_follow_up,
                    response_date=response_date,
                    interview_date=interview_date,
                    salary_expected=salary_expected,
                    salary_offered=salary_offered,
                    application_channel=channel,
                    recruiter_name=recruiter_name,
                    recruiter_email=recruiter_email,
                    recruiter_phone=recruiter_phone,
                    feedback=feedback,
                    notes=notes,
                )
            else:
                self.application_service.update_application(
                    self.current_application_id,
                    job_id=int(job_id),
                    company_id=int(company_id),
                    status=status,
                    application_date=application_date,
                    next_follow_up=next_follow_up,
                    response_date=response_date,
                    interview_date=interview_date,
                    salary_expected=salary_expected,
                    salary_offered=salary_offered,
                    application_channel=channel,
                    recruiter_name=recruiter_name,
                    recruiter_email=recruiter_email,
                    recruiter_phone=recruiter_phone,
                    feedback=feedback,
                    notes=notes,
                )

            self._clear_form()
            self._load_applications()
        except ValueError as exc:
            QMessageBox.warning(self, "Dados inválidos", str(exc))
        except Exception as exc:  # pragma: no cover - defensive UI handling
            QMessageBox.critical(self, "Erro", str(exc))

    def _delete_application(self) -> None:
        if self.current_application_id is None:
            return
        confirmation = QMessageBox.question(
            self,
            "Confirmar exclusão",
            "Deseja excluir esta candidatura?",
        )
        if confirmation != QMessageBox.Yes:
            return
        self.application_service.delete_application(self.current_application_id)
        self._clear_form()
        self._load_applications()

    def _on_row_selected(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        self.current_application_id = int(self.table.item(row, 0).text())

    def _load_applications(self) -> None:
        applications = self.application_service.list_applications()
        self._render_applications(applications)

    def _filter_applications(self) -> None:
        status = self.filter_status_combo.currentText() or None
        company_id = self.filter_company_combo.currentData()
        query = self.search_input.text().strip()
        if query:
            applications = self.application_service.search_applications(query)
        elif status or company_id is not None:
            applications = self.application_service.filter_applications(
                status=status,
                company_id=int(company_id) if company_id is not None else None,
            )
        else:
            applications = self.application_service.list_applications()
        self._render_applications(applications)

    def _render_applications(self, applications: list) -> None:
        self.table.setRowCount(len(applications))
        for row, application in enumerate(applications):
            self.table.setItem(row, 0, QTableWidgetItem(str(application.id)))
            self.table.setItem(
                row, 1, QTableWidgetItem(application.company.name if application.company else "")
            )
            self.table.setItem(
                row, 2, QTableWidgetItem(application.job.title if application.job else "")
            )
            self.table.setItem(row, 3, QTableWidgetItem(application.status))
            self.table.setItem(
                row,
                4,
                QTableWidgetItem(
                    application.application_date.strftime("%d/%m/%Y")
                    if application.application_date
                    else ""
                ),
            )
            self.table.setItem(
                row,
                5,
                QTableWidgetItem(
                    application.next_follow_up.strftime("%d/%m/%Y")
                    if application.next_follow_up
                    else ""
                ),
            )
        self.table.resizeColumnsToContents()

    def _clear_form(self) -> None:
        self.current_application_id = None
        self.company_combo.setCurrentIndex(0)
        self.job_combo.clear()
        self.status_combo.setCurrentIndex(0)
        self.application_date_input.setDate(self.application_date_input.minimumDate())
        self.next_follow_up_input.setDate(self.next_follow_up_input.minimumDate())
        self.response_date_input.setDate(self.response_date_input.minimumDate())
        self.interview_date_input.setDate(self.interview_date_input.minimumDate())
        self.salary_expected_input.clear()
        self.salary_offered_input.clear()
        self.channel_input.clear()
        self.recruiter_name_input.clear()
        self.recruiter_email_input.clear()
        self.recruiter_phone_input.clear()
        self.feedback_input.clear()
        self.notes_input.clear()

    def _parse_optional_number(self, value: str) -> float | None:
        if not value.strip():
            return None
        return float(value)
