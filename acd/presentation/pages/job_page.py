from __future__ import annotations

from PySide6.QtCore import (
    QDate,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
)

from acd.presentation.pages.base_page import BasePage
from acd.services.company_service import CompanyService
from acd.services.job_service import JobService


class JobPage(BasePage):
    """Página de cadastro e gerenciamento de vagas."""

    def __init__(self) -> None:
        super().__init__("Vagas")

        self.job_service = JobService()
        self.company_service = CompanyService()
        self.current_job_id: int | None = None
        self.company_combo = QComboBox()
        self.title_input = QLineEdit()
        self.location_input = QLineEdit()
        self.work_model_combo = QComboBox()
        self.employment_type_combo = QComboBox()
        self.salary_min_input = QDoubleSpinBox()
        self.salary_min_input.setDecimals(2)
        self.salary_min_input.setMaximum(99999999.99)
        self.salary_min_input.setMinimum(0)
        self.salary_min_input.setSingleStep(100)
        self.salary_min_input.setGroupSeparatorShown(True)
        self.salary_min_input.setPrefix("R$ ")
        self.salary_max_input = QDoubleSpinBox()
        self.salary_max_input.setDecimals(2)
        self.salary_max_input.setMaximum(99999999.99)
        self.salary_max_input.setMinimum(0)
        self.salary_max_input.setSingleStep(100)
        self.salary_max_input.setGroupSeparatorShown(True)
        self.salary_max_input.setPrefix("R$ ")
        self.currency_input = QComboBox()

        # self.currency_input.addItems(
        #     [
        #         "R$",
        #         "US$",
        #         "€",
        #         "£",
        #     ]
        # )

        self.status_combo = QComboBox()
        self.source_input = QLineEdit()
        self.url_input = QLineEdit()
        self.recruiter_input = QLineEdit()
        self.deadline_input = QDateEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDisplayFormat("dd/MM/yyyy")
        self.deadline_input.setDate(QDate.currentDate())
        self.application_date_input = QDateEdit()
        self.application_date_input.setCalendarPopup(True)
        self.application_date_input.setDate(QDate.currentDate())
        self.priority_input = QSpinBox()
        self.priority_input.setMinimum(1)
        self.priority_input.setMaximum(5)
        self.priority_input.setValue(3)
        self.notes_input = QTextEdit()
        self.search_input = QLineEdit()
        self.filter_status_combo = QComboBox()
        self.filter_company_combo = QComboBox()
        self.filter_button = QPushButton("Filtrar")
        self.save_button = QPushButton("Salvar")
        self.delete_button = QPushButton("Excluir")
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Empresa", "Cargo", "Status", "Cidade", "Cadastro"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self._setup_controls()
        self._load_companies()
        self._load_jobs()

    def _setup_controls(self) -> None:
        self.company_combo.addItem("", "")
        self.currency_input.addItems(
            [
                "BRL",
                "USD",
                "EUR",
                "GBP",
            ]
        )
        self.currency_input.currentIndexChanged.connect(self._update_currency_symbol)

        self._update_currency_symbol()

        self.work_model_combo.addItems(["", "Presencial", "Híbrido", "Remoto"])
        self.employment_type_combo.addItems(
            ["", "CLT", "PJ", "Temporário", "Estágio", "Freelancer", "Terceirizado"]
        )
        self.status_combo.addItems(
            [
                "Nova",
                "Analisada",
                "Currículo Enviado",
                "Carta Enviada",
                "Inscrição Concluída",
                "Triagem RH",
                "Entrevista RH",
                "Entrevista Técnica",
                "Teste",
                "Oferta",
                "Rejeitada",
                "Encerrada",
            ]
        )
        self.filter_status_combo.addItem("", "")
        self.filter_status_combo.addItems(
            self.status_combo.itemText(index) for index in range(1, self.status_combo.count())
        )
        self.filter_company_combo.addItem("", "")

        form = QFormLayout()
        form.addRow(QLabel("Empresa"), self.company_combo)
        form.addRow(QLabel("Cargo"), self.title_input)
        form.addRow(QLabel("Cidade"), self.location_input)
        form.addRow(QLabel("Modelo"), self.work_model_combo)
        form.addRow(QLabel("Tipo"), self.employment_type_combo)
        form.addRow(QLabel("Salário mín."), self.salary_min_input)
        form.addRow(QLabel("Salário máx."), self.salary_max_input)
        form.addRow(QLabel("Moeda"), self.currency_input)
        form.addRow(QLabel("Status"), self.status_combo)
        form.addRow(QLabel("Fonte"), self.source_input)
        form.addRow(QLabel("Link"), self.url_input)
        form.addRow(QLabel("Recrutador"), self.recruiter_input)
        form.addRow(QLabel("Prazo"), self.deadline_input)
        form.addRow(QLabel("Data aplicação"), self.application_date_input)
        form.addRow(QLabel("Prioridade"), self.priority_input)
        form.addRow(QLabel("Observações"), self.notes_input)

        actions = QHBoxLayout()
        actions.addWidget(self.save_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        self.save_button.clicked.connect(self._save_job)
        self.delete_button.clicked.connect(self._delete_job)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_button)
        self.filter_button.clicked.connect(self._filter_jobs)

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

    def _save_job(self) -> None:
        try:
            company_id = self.company_combo.currentData()
            title = self.title_input.text().strip()
            location = self.location_input.text().strip()
            work_model = self.work_model_combo.currentText()
            employment_type = self.employment_type_combo.currentText()
            salary_min = self.salary_min_input.value()
            salary_max = self.salary_max_input.value()
            currency = self.currency_input.currentText()
            status = self.status_combo.currentText()
            source = self.source_input.text().strip()
            job_url = self.url_input.text().strip()
            recruiter = self.recruiter_input.text().strip()
            deadline = (
                self.deadline_input.date().toString("yyyy-MM-dd")
                if self.deadline_input.date().isValid()
                else ""
            )
            application_date = (
                self.application_date_input.date().toString("yyyy-MM-dd")
                if self.application_date_input.date().isValid()
                else ""
            )
            priority = self.priority_input.value()
            notes = self.notes_input.toPlainText().strip()

            if self.current_job_id is None:
                self.job_service.create_job(
                    company_id=int(company_id),
                    title=title,
                    location=location,
                    work_model=work_model,
                    employment_type=employment_type,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    currency=currency,
                    status=status,
                    source=source,
                    job_url=job_url,
                    recruiter=recruiter,
                    application_deadline=deadline,
                    application_date=application_date,
                    priority=priority,
                    notes=notes,
                )
            else:
                self.job_service.update_job(
                    self.current_job_id,
                    company_id=int(company_id),
                    title=title,
                    location=location,
                    work_model=work_model,
                    employment_type=employment_type,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    currency=currency,
                    status=status,
                    source=source,
                    job_url=job_url,
                    recruiter=recruiter,
                    application_deadline=deadline,
                    application_date=application_date,
                    priority=priority,
                    notes=notes,
                )

            self._clear_form()
            self._load_jobs()
        except ValueError as exc:
            QMessageBox.warning(self, "Dados inválidos", str(exc))
        except Exception as exc:  # pragma: no cover - defensive UI handling
            QMessageBox.critical(self, "Erro", str(exc))

    def _delete_job(self) -> None:
        if self.current_job_id is None:
            return

        confirmation = QMessageBox.question(
            self,
            "Confirmar exclusão",
            "Deseja excluir esta vaga?",
        )
        if confirmation != QMessageBox.Yes:
            return

        self.job_service.delete_job(self.current_job_id)
        self._clear_form()
        self._load_jobs()

    def _on_row_selected(self) -> None:
        """Carrega todos os dados da vaga selecionada."""

        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            return

        row = selected_rows[0].row()

        self.current_job_id = int(self.table.item(row, 0).text())

        job = self.job_service.get_job(self.current_job_id)

        if job is None:
            return

        self._populate_form(job)

    def _populate_form(self, job) -> None:
        """Preenche o formulário com os dados da vaga."""

        index = self.company_combo.findData(job.company_id)

        if index >= 0:
            self.company_combo.setCurrentIndex(index)

        self.title_input.setText(job.title or "")
        self.location_input.setText(job.location or "")

        self.work_model_combo.setCurrentText(job.work_model or "")

        self.employment_type_combo.setCurrentText(job.employment_type or "")

        self.salary_min_input.setValue(float(job.salary_min or 0))

        self.salary_max_input.setValue(float(job.salary_max or 0))

        index = self.currency_input.findText(job.currency or "R$")

        if index >= 0:
            self.currency_input.setCurrentIndex(index)

        self._update_currency_symbol()

        self.status_combo.setCurrentText(job.status or "Nova")

        self.source_input.setText(job.source or "")

        self.url_input.setText(job.job_url or "")

        self.recruiter_input.setText(job.recruiter or "")

        if job.application_deadline:
            self.deadline_input.setDate(job.application_deadline)

        if job.application_date:
            self.application_date_input.setDate(job.application_date)

        self.priority_input.setValue(job.priority or 3)

        self.notes_input.setPlainText(job.notes or "")

    def _load_jobs(self) -> None:
        jobs = self.job_service.list_jobs()
        self._render_jobs(jobs)

    def _filter_jobs(self) -> None:
        company_id = self.filter_company_combo.currentData()
        status = self.filter_status_combo.currentText() or None
        query = self.search_input.text().strip()

        if query:
            jobs = self.job_service.search_jobs(query)
        elif company_id is not None or status:
            jobs = self.job_service.filter_jobs(
                company_id=int(company_id) if company_id is not None else None,
                status=status,
            )
        else:
            jobs = self.job_service.list_jobs()
        self._render_jobs(jobs)

    def _render_jobs(self, jobs: list) -> None:
        self.table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            self.table.setItem(row, 0, QTableWidgetItem(str(job.id)))
            self.table.setItem(row, 1, QTableWidgetItem(job.company.name if job.company else ""))
            self.table.setItem(row, 2, QTableWidgetItem(job.title))
            self.table.setItem(row, 3, QTableWidgetItem(job.status or ""))
            self.table.setItem(row, 4, QTableWidgetItem(job.location or ""))
            self.table.setItem(
                row,
                5,
                QTableWidgetItem(job.created_at.strftime("%d/%m/%Y") if job.created_at else ""),
            )
        self.table.resizeColumnsToContents()

    def _clear_form(self) -> None:
        """Limpa o formulário e prepara para um novo cadastro."""
        self.current_job_id = None
        self.company_combo.setCurrentIndex(0)
        self.title_input.clear()
        self.location_input.clear()
        self.work_model_combo.setCurrentIndex(0)
        self.employment_type_combo.setCurrentIndex(0)
        self.salary_min_input.setValue(0.00)
        self.salary_max_input.setValue(0.00)
        self.currency_input.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.source_input.clear()
        self.url_input.clear()
        self.recruiter_input.clear()
        # Reinicia as datas para a data atual
        self.deadline_input.setDate(QDate.currentDate())
        self.application_date_input.setDate(QDate.currentDate())
        self.priority_input.setValue(3)
        self.notes_input.clear()
        # Remove seleção da tabela
        self.table.clearSelection()
        # Coloca o foco no primeiro campo útil
        self.title_input.setFocus()

    def _update_currency_symbol(self) -> None:
        """Atualiza o prefixo dos campos de salário conforme a moeda."""

        symbols = {
            "BRL": "R$",
            "USD": "US$",
            "EUR": "€",
            "GBP": "£",
        }

        symbol = symbols.get(
            self.currency_input.currentText(),
            "R$",
        )

        self.salary_min_input.setPrefix(f"{symbol} ")
        self.salary_max_input.setPrefix(f"{symbol} ")

    def _parse_optional_number(self, value: str) -> float | None:
        if not value.strip():
            return None
        return float(value)
