from __future__ import annotations

from PySide6.QtCore import (
    QDate,
    QThread,
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
from sqlalchemy.exc import IntegrityError

from acd.presentation.pages.base_page import BasePage
from acd.presentation.pages.linkedin_job_import_worker import LinkedInJobImportWorker
from acd.services.company_name_matcher import find_company_name_candidate
from acd.services.company_service import CompanyService
from acd.services.job_service import JobService
from acd.services.linkedin_job_import_service import (
    ImportedLinkedInJob,
    LinkedInJobImportError,
    LinkedInJobImportService,
)


class JobPage(BasePage):
    """Página de cadastro e gerenciamento de vagas."""

    def __init__(self, job_service: JobService, company_service: CompanyService) -> None:
        super().__init__("Vagas")

        self.job_service = job_service
        self.company_service = company_service
        self.current_job_id: int | None = None
        self._import_thread: QThread | None = None
        self._import_worker: LinkedInJobImportWorker | None = None
        self._job_import_service = LinkedInJobImportService()
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
        self.url_input.setPlaceholderText(
            "Cole a URL da vaga do LinkedIn e clique em Importar vaga"
        )
        self.import_linkedin_button = QPushButton("Importar vaga do LinkedIn")
        self.import_status_label = QLabel("")
        self.recruiter_input = QLineEdit()
        self.deadline_input = QDateEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDisplayFormat("dd/MM/yyyy")
        self.deadline_input.setDate(QDate.currentDate())
        self.application_date_input = QDateEdit()
        self.application_date_input.setCalendarPopup(True)
        self.application_date_input.setDisplayFormat("dd/MM/yyyy")
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
        self.table.verticalHeader().hide()
        self.table.setCornerButtonEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().hide()
        self.table.setCornerButtonEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self._setup_controls()
        self._load_companies()
        self._load_jobs()

    def refresh_reference_data(self) -> None:
        """Atualiza empresas e vagas ao entrar na página."""
        selected_company = self.company_combo.currentData()
        self._load_companies()
        if selected_company not in (None, ""):
            index = self.company_combo.findData(selected_company)
            if index >= 0:
                self.company_combo.setCurrentIndex(index)
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
        self.status_combo.addItems(JobService.JOB_STATUSES)
        self.filter_status_combo.addItem("", "")
        self.filter_status_combo.addItems(JobService.JOB_STATUSES)
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
        link_layout = QHBoxLayout()
        link_layout.addWidget(self.url_input)
        link_layout.addWidget(self.import_linkedin_button)
        form.addRow(QLabel("Link"), link_layout)
        form.addRow(QLabel("Importação"), self.import_status_label)
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
        self.import_linkedin_button.clicked.connect(self._import_linkedin_job)

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

    def _import_linkedin_job(self) -> None:
        url = self.url_input.text().strip()
        try:
            normalized_url = self._job_import_service.normalize_linkedin_job_url(url)
        except LinkedInJobImportError as exc:
            QMessageBox.warning(self, "Importar vaga", str(exc))
            return

        if self.job_service.job_url_exists(
            normalized_url,
            exclude_job_id=self.current_job_id,
        ):
            QMessageBox.warning(
                self,
                "Vaga já cadastrada",
                "Esta URL já está vinculada a uma vaga cadastrada no ACD.",
            )
            return

        self.url_input.setText(normalized_url)
        self.import_linkedin_button.setEnabled(False)
        self.import_status_label.setText("Importando vaga...")

        thread = QThread(self)
        worker = LinkedInJobImportWorker(self._job_import_service, normalized_url)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._on_linkedin_import_succeeded)
        worker.failed.connect(self._on_linkedin_import_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_linkedin_import_finished)
        self._import_thread = thread
        self._import_worker = worker
        thread.start()

    def _on_linkedin_import_succeeded(self, result: ImportedLinkedInJob) -> None:
        if not result.title and not result.company_name and not result.description:
            QMessageBox.warning(
                self,
                "Importação incompleta",
                "Não foram encontrados dados públicos suficientes para preencher a vaga.",
            )
            return

        has_existing_data = any(
            (
                self.title_input.text().strip(),
                self.location_input.text().strip(),
                self.notes_input.toPlainText().strip(),
            )
        )
        if has_existing_data:
            confirmation = QMessageBox.question(
                self,
                "Substituir dados",
                "O formulário já possui informações. Deseja substituir os campos "
                "disponíveis pelos dados importados?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if confirmation != QMessageBox.Yes:
                self.import_status_label.setText("Importação cancelada pelo usuário.")
                return

        self._apply_imported_job(result)
        self.import_status_label.setText("Vaga importada. Revise os dados antes de salvar.")

    def _apply_imported_job(self, result: ImportedLinkedInJob) -> None:
        self.title_input.setText(result.title)
        self.location_input.setText(result.location)
        if result.work_model:
            self.work_model_combo.setCurrentText(result.work_model)
        if result.employment_type:
            self.employment_type_combo.setCurrentText(result.employment_type)
        if result.salary_min is not None:
            self.salary_min_input.setValue(result.salary_min)
        if result.salary_max is not None:
            self.salary_max_input.setValue(result.salary_max)
        if result.currency:
            self.currency_input.setCurrentText(result.currency)
            self._update_currency_symbol()
        self.source_input.setText("LinkedIn")
        self.url_input.setText(result.source_url)
        self.recruiter_input.setText(result.recruiter)
        if result.application_deadline:
            deadline = QDate.fromString(result.application_deadline, "yyyy-MM-dd")
            if deadline.isValid():
                self.deadline_input.setDate(deadline)
        notes = result.notes_text()
        if notes:
            self.notes_input.setPlainText(notes)

        company_matched = self._select_imported_company(result.company_name)
        if result.company_name and not company_matched:
            QMessageBox.information(
                self,
                "Empresa não cadastrada",
                f'A empresa "{result.company_name}" foi identificada, mas ainda não existe '
                "no cadastro do ACD. Cadastre-a na página Empresas e depois selecione-a "
                "antes de salvar a vaga.",
            )

    def _select_imported_company(self, company_name: str) -> bool:
        candidate = find_company_name_candidate(
            company_name,
            (
                (index, self.company_combo.itemText(index))
                for index in range(1, self.company_combo.count())
            ),
        )
        if candidate is None:
            return False

        if not candidate.exact:
            confirmation = QMessageBox.question(
                self,
                "Empresa semelhante encontrada",
                f'A vaga informa "{company_name}", mas foi encontrada a empresa '
                f'cadastrada "{candidate.name}".\n\nDeseja vincular a vaga a essa empresa?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if confirmation != QMessageBox.Yes:
                return False

        self.company_combo.setCurrentIndex(candidate.index)
        return True

    def _on_linkedin_import_failed(self, message: str) -> None:
        self.import_status_label.setText("Falha na importação.")
        QMessageBox.critical(self, "Não foi possível importar", message)

    def _on_linkedin_import_finished(self) -> None:
        self.import_linkedin_button.setEnabled(True)
        self._import_thread = None
        self._import_worker = None

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

            if company_id in (None, ""):
                raise ValueError("Selecione uma empresa.")
            company_id_value = int(company_id)

            if self.current_job_id is None:
                self.job_service.create_job(
                    company_id=company_id_value,
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
                    company_id=company_id_value,
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
            QMessageBox.information(self, "Vaga", "Selecione uma vaga para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Confirmar exclusão",
            "Deseja excluir esta vaga?",
        )
        if confirmation != QMessageBox.Yes:
            return

        try:
            deleted = self.job_service.delete_job(self.current_job_id)
            if not deleted:
                QMessageBox.warning(self, "Vaga", "A vaga não pôde ser excluída.")
                return
            self._clear_form()
            self._load_jobs()
        except IntegrityError:
            cascade_confirmation = QMessageBox.question(
                self,
                "Registros vinculados",
                "Esta vaga possui candidaturas e demais registros vinculados.\n\n"
                "Deseja excluir também todos os registros vinculados? "
                "Esta operação não poderá ser desfeita.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if cascade_confirmation != QMessageBox.Yes:
                return
            try:
                deleted = self.job_service.delete_job(
                    self.current_job_id,
                    delete_linked=True,
                )
                if not deleted:
                    QMessageBox.warning(
                        self,
                        "Vaga",
                        "O registro não pôde ser excluído.",
                    )
                    return
                self._clear_form()
                self._load_jobs()
            except Exception:
                QMessageBox.critical(
                    self,
                    "Não foi possível excluir",
                    "Não foi possível excluir o registro e seus vínculos.",
                )
        except Exception as exc:  # pragma: no cover - defensive UI handling
            QMessageBox.critical(
                self,
                "Não foi possível excluir",
                f"A vaga possui registros vinculados ou ocorreu um erro:\n{exc}",
            )

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
        company_id_data = self.filter_company_combo.currentData()
        company_id = (
            int(company_id_data)
            if company_id_data not in (None, "")
            else None
        )
        status = self.filter_status_combo.currentText() or None
        query = self.search_input.text().strip()

        if query:
            jobs = self.job_service.search_jobs(query)
        elif company_id is not None or status:
            jobs = self.job_service.filter_jobs(
                company_id=company_id,
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
        self.import_status_label.clear()
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
