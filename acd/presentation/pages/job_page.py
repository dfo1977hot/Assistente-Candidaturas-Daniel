from __future__ import annotations

from PySide6.QtCore import QDate, QLocale
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
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

from acd.presentation.dialogs.linkedin_saved_jobs_progress_dialog import (
    LinkedInSavedJobsProgressDialog,
)
from acd.presentation.long_running_task_executor import LongRunningTaskExecutor
from acd.presentation.pages.base_page import BasePage
from acd.services.closed_linkedin_jobs_registry import ClosedLinkedInJobsRegistry
from acd.services.company_name_matcher import find_company_name_candidate
from acd.services.company_service import CompanyService
from acd.services.job_service import JobService
from acd.services.linkedin_application_resolver import (
    LinkedInApplicationResolution,
    LinkedInApplicationResolver,
    UnavailableLinkedInApplicationResolver,
)
from acd.services.linkedin_job_import_service import (
    ImportedLinkedInJob,
    LinkedInJobImportError,
    LinkedInJobImportService,
)
from acd.services.linkedin_saved_jobs_import_service import (
    LinkedInSavedJobsImportService,
    SavedJobsImportResult,
    SavedJobsProgress,
)
from acd.services.recruiter_email_research_service import (
    RecruiterEmailResearchRequest,
    RecruiterEmailResearchService,
)
from acd.services.salary_research_service import (
    SalaryResearchRequest,
    SalaryResearchResult,
    SalaryResearchService,
)


class JobPage(BasePage):
    """Página de cadastro e gerenciamento de vagas."""

    def __init__(
        self,
        job_service: JobService,
        company_service: CompanyService,
        job_import_service: LinkedInJobImportService | None = None,
        saved_jobs_import_service: LinkedInSavedJobsImportService | None = None,
        salary_research_service: SalaryResearchService | None = None,
        recruiter_email_research_service: RecruiterEmailResearchService | None = None,
        application_url_resolver: LinkedInApplicationResolver | None = None,
    ) -> None:
        super().__init__("Vagas")

        self.job_service = job_service
        self.company_service = company_service
        self.current_job_id: int | None = None
        self._import_executor = LongRunningTaskExecutor(self)
        self._import_executor.succeeded.connect(self._on_linkedin_import_succeeded)
        self._import_executor.failed.connect(self._on_linkedin_import_failed)
        self._import_executor.finished.connect(self._on_linkedin_import_finished)
        self._job_import_service = job_import_service
        self._closed_jobs_registry = getattr(
            job_import_service,
            "_closed_jobs_registry",
            ClosedLinkedInJobsRegistry(),
        )
        self._application_url_resolver = (
            application_url_resolver or UnavailableLinkedInApplicationResolver()
        )
        self._application_url_executor = LongRunningTaskExecutor(self)
        self._application_url_executor.progress.connect(
            self._on_application_url_progress
        )
        self._application_url_executor.succeeded.connect(
            self._on_application_url_resolved
        )
        self._application_url_executor.failed.connect(
            self._on_application_url_resolution_failed
        )
        self._application_url_executor.finished.connect(
            self._on_application_url_resolution_finished
        )
        self._saved_jobs_import_service = saved_jobs_import_service
        self._salary_research_service = salary_research_service
        self._recruiter_email_research_service = recruiter_email_research_service
        self._recruiter_email_executor = LongRunningTaskExecutor(self)
        self._recruiter_email_executor.succeeded.connect(
            self._on_recruiter_email_research_succeeded
        )
        self._salary_research_executor = LongRunningTaskExecutor(self)
        self._salary_research_executor.succeeded.connect(
            self._on_salary_research_succeeded
        )
        self._salary_research_executor.failed.connect(
            self._on_salary_research_failed
        )
        self._salary_research_executor.finished.connect(
            self._on_salary_research_finished
        )
        self._saved_jobs_dialog: LinkedInSavedJobsProgressDialog | None = None
        self._saved_jobs_executor = LongRunningTaskExecutor(self)
        self._saved_jobs_executor.progress.connect(self._on_saved_jobs_progress)
        self._saved_jobs_executor.succeeded.connect(self._on_saved_jobs_succeeded)
        self._saved_jobs_executor.failed.connect(self._on_saved_jobs_failed)
        self._saved_jobs_executor.cancelled.connect(self._on_saved_jobs_cancelled)
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
        self.salary_min_input.setSpecialValueText("A combinar")
        self.salary_min_input.setLocale(QLocale(QLocale.Portuguese, QLocale.Brazil))
        self.salary_min_input.setPrefix("R$ ")
        self.salary_max_input = QDoubleSpinBox()
        self.salary_max_input.setDecimals(2)
        self.salary_max_input.setMaximum(99999999.99)
        self.salary_max_input.setMinimum(0)
        self.salary_max_input.setSingleStep(100)
        self.salary_max_input.setGroupSeparatorShown(True)
        self.salary_max_input.setLocale(QLocale(QLocale.Portuguese, QLocale.Brazil))
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
        self.application_url_input = QLineEdit()
        self.application_url_input.setPlaceholderText(
            "Cole a URL externa em que a candidatura é realmente enviada"
        )
        self.detect_application_url_button = QPushButton("Detectar link Candidatar-se")
        self.import_linkedin_button = QPushButton("Importar vaga do LinkedIn")
        self.import_saved_jobs_button = QPushButton("Importar vagas salvas do LinkedIn")
        self.import_status_label = QLabel("")
        self.recruiter_input = QLineEdit()
        self.recruiter_email_input = QLineEdit()
        self.recruiter_email_input.setPlaceholderText("E-mail profissional público")
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
        self.notes_input.setMaximumHeight(90)
        self.benefits_input = QTextEdit()
        self.benefits_input.setMaximumHeight(90)
        self.search_input = QLineEdit()
        self.filter_status_combo = QComboBox()
        self.filter_company_combo = QComboBox()
        self.filter_button = QPushButton("Filtrar")
        self.save_button = QPushButton("Salvar")
        self.delete_button = QPushButton("Excluir")
        self.salary_research_button = QPushButton("Pesquisar média salarial com IA")
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


        form_columns = QHBoxLayout()

        first_column = QFormLayout()
        first_column.addRow(QLabel("Empresa"), self.company_combo)
        first_column.addRow(QLabel("Cargo"), self.title_input)
        first_column.addRow(QLabel("Cidade"), self.location_input)
        first_column.addRow(QLabel("Modelo"), self.work_model_combo)
        first_column.addRow(QLabel("Tipo"), self.employment_type_combo)
        first_column.addRow(QLabel("Status"), self.status_combo)

        second_column = QFormLayout()
        second_column.addRow(QLabel("Remuneração oferecida"), self.salary_min_input)
        second_column.addRow(QLabel("Remuneração ideal"), self.salary_max_input)
        second_column.addRow(QLabel("Moeda"), self.currency_input)
        second_column.addRow(QLabel("Fonte"), self.source_input)
        second_column.addRow(QLabel("Recrutador"), self.recruiter_input)
        second_column.addRow(QLabel("E-mail"), self.recruiter_email_input)
        second_column.addRow(QLabel("Prioridade"), self.priority_input)

        third_column = QFormLayout()
        third_column.addRow(QLabel("Prazo"), self.deadline_input)
        third_column.addRow(QLabel("Data aplicação"), self.application_date_input)
        third_column.addRow(QLabel("Importação"), self.import_status_label)

        form_columns.addLayout(first_column, 1)
        form_columns.addLayout(second_column, 1)
        form_columns.addLayout(third_column, 1)

        full_width_fields = QFormLayout()
        link_layout = QHBoxLayout()
        link_layout.addWidget(self.url_input)
        link_layout.addWidget(self.import_linkedin_button)
        full_width_fields.addRow(QLabel("Link da vaga"), link_layout)

        application_url_layout = QHBoxLayout()
        application_url_layout.addWidget(self.application_url_input)
        application_url_layout.addWidget(self.detect_application_url_button)
        full_width_fields.addRow(QLabel("URL da candidatura"), application_url_layout)
        full_width_fields.addRow(QLabel("Benefícios e valores"), self.benefits_input)
        full_width_fields.addRow(QLabel("Observações"), self.notes_input)

        actions = QGridLayout()
        action_buttons = (
            self.save_button,
            self.delete_button,
            self.import_saved_jobs_button,
            self.salary_research_button,
        )
        for column, button in enumerate(action_buttons):
            actions.addWidget(button, 0, column)
        self.save_button.clicked.connect(self._save_current_job)
        self.delete_button.clicked.connect(self._delete_job)
        self.import_linkedin_button.clicked.connect(self._import_linkedin_job)
        self.detect_application_url_button.clicked.connect(self._detect_application_url)
        self.import_saved_jobs_button.clicked.connect(self._import_saved_linkedin_jobs)
        self.salary_research_button.clicked.connect(self._research_salary)

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

        self.layout.addLayout(search_layout)
        self.layout.addLayout(filter_layout)
        self.layout.addWidget(self.table)
        self.layout.addLayout(form_columns)
        self.layout.addLayout(full_width_fields)
        self.layout.addLayout(actions)

    def _load_companies(self) -> None:
        companies = self.company_service.list_companies()
        self.company_combo.clear()
        self.company_combo.addItem("", "")
        self.filter_company_combo.clear()
        self.filter_company_combo.addItem("", "")
        for company in companies:
            self.company_combo.addItem(company.name, company.id)
            self.filter_company_combo.addItem(company.name, company.id)

    def _import_saved_linkedin_jobs(self) -> None:
        if self._saved_jobs_import_service is None:
            QMessageBox.warning(
                self,
                "Importar vagas salvas",
                "O serviço de importação em lote não está disponível.",
            )
            return
        dialog = LinkedInSavedJobsProgressDialog(self)
        dialog.cancel_requested.connect(self._saved_jobs_executor.cancel)
        self._saved_jobs_dialog = dialog
        service = self._saved_jobs_import_service
        self.import_saved_jobs_button.setEnabled(False)

        def task(progress_emit, cancellation_token):
            return service.import_saved_jobs(
                progress_callback=progress_emit,
                cancellation_requested=lambda: cancellation_token.is_cancellation_requested,
            )

        self._saved_jobs_executor.execute_with_context(task)
        dialog.open()

    def _on_saved_jobs_progress(self, progress: object) -> None:
        if self._saved_jobs_dialog is not None and isinstance(progress, SavedJobsProgress):
            self._saved_jobs_dialog.update_progress(progress)

    def _on_saved_jobs_succeeded(self, result: object) -> None:
        if self._saved_jobs_dialog is not None and isinstance(result, SavedJobsImportResult):
            self._saved_jobs_dialog.show_result(result)
            QMessageBox.information(
                self,
                "Importação concluída",
                (
                    f"Importadas: {result.imported}\n"
                    f"Já existentes: {result.existing}\n"
                    f"Excluídas por não aceitarem mais candidaturas: {result.deleted}\n"
                    f"Falhas: {result.failed}"
                ),
            )
        self._load_companies()
        self._load_jobs()
        self.import_saved_jobs_button.setEnabled(True)

    def _on_saved_jobs_failed(self, error: object) -> None:
        if self._saved_jobs_dialog is not None:
            self._saved_jobs_dialog.show_failure(str(error))
        self.import_saved_jobs_button.setEnabled(True)

    def _on_saved_jobs_cancelled(self) -> None:
        if self._saved_jobs_dialog is not None:
            self._saved_jobs_dialog.show_cancelled()
        self.import_saved_jobs_button.setEnabled(True)

    def _import_linkedin_job(self) -> None:
        if self._job_import_service is None:
            QMessageBox.warning(
                self,
                "Importar vaga",
                "O serviço de importação não está disponível.",
            )
            return

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

        service = self._job_import_service
        self._import_executor.execute(lambda: service.import_from_url(normalized_url))

    def _on_linkedin_import_succeeded(self, result: ImportedLinkedInJob) -> None:
        if result.accepting_applications is False:
            deleted = self._delete_closed_imported_job(result)
            self.import_status_label.setText(
                "Vaga encerrada: excluída e bloqueada para novas importações."
            )
            self._load_jobs()
            if deleted:
                self._clear_form()
            QMessageBox.information(
                self,
                "Vaga encerrada",
                "O anúncio não aceita mais candidaturas. "
                "A vaga foi excluída do ACD e não será importada novamente.",
            )
            return

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
        self._research_recruiter_email_if_needed(result)
        self.import_status_label.setText("Vaga importada. Revise os dados antes de salvar.")
        if not self.application_url_input.text().strip():
            self._detect_application_url()

    def _delete_closed_imported_job(self, result: ImportedLinkedInJob) -> bool:
        """Delete a persisted vacancy when LinkedIn reports applications closed."""

        job = None
        if self.current_job_id is not None:
            job = self.job_service.get_job(self.current_job_id)
        if job is None and result.source_url:
            job = self.job_service.get_job_by_url(result.source_url)
        if job is None and result.linkedin_job_id:
            job = self.job_service.get_job_by_linkedin_job_id(
                result.linkedin_job_id
            )
        if job is None or job.id is None:
            return False
        deleted = self.job_service.delete_job(int(job.id), delete_linked=True)
        if deleted:
            self.current_job_id = None
        return deleted

    def _research_recruiter_email_if_needed(
        self,
        result: ImportedLinkedInJob,
    ) -> None:
        if self.recruiter_email_input.text().strip():
            return
        service = self._recruiter_email_research_service
        if service is None or not result.company_name.strip():
            return

        request = RecruiterEmailResearchRequest(
            company_name=result.company_name,
            job_title=result.title,
            location=result.location,
            recruiter_name=result.recruiter,
        )
        self._recruiter_email_executor.execute(
            lambda: service.research(request),
            timeout_ms=90_000,
        )

    def _on_recruiter_email_research_succeeded(self, result: object) -> None:
        email = str(result or "").strip()
        if email and not self.recruiter_email_input.text().strip():
            self.recruiter_email_input.setText(email)

    def _apply_imported_job(self, result: ImportedLinkedInJob) -> None:
        self.title_input.setText(result.title)
        self.location_input.setText(result.location)
        self.work_model_combo.setCurrentText(result.work_model or "Presencial")
        if result.employment_type:
            self.employment_type_combo.setCurrentText(result.employment_type)
        advertised_values = [
            value for value in (result.salary_min, result.salary_max) if value is not None
        ]
        self._set_offered_remuneration(max(advertised_values) if advertised_values else None)
        self.salary_max_input.setValue(0.00)
        if result.currency:
            self.currency_input.setCurrentText(result.currency)
            self._update_currency_symbol()
        self.source_input.setText("LinkedIn")
        self.url_input.setText(result.source_url)
        imported_application_url = str(
            getattr(result, "application_url", "") or ""
        ).strip()
        if imported_application_url:
            self.application_url_input.setText(imported_application_url)
        self.recruiter_input.setText(result.recruiter)
        self.recruiter_email_input.setText(
            str(getattr(result, "recruiter_email", "") or "")
        )
        if result.application_deadline:
            deadline = QDate.fromString(result.application_deadline, "yyyy-MM-dd")
            if deadline.isValid():
                self.deadline_input.setDate(deadline)
        benefits_text = self._format_benefits(getattr(result, "benefits", ""))
        if benefits_text:
            self.benefits_input.setPlainText(benefits_text)
        notes = result.notes_text()
        if notes:
            self.notes_input.setPlainText(self._strip_benefits_marker(notes))

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

    def _detect_application_url(self) -> None:
        job_url = self.url_input.text().strip()
        if not job_url:
            QMessageBox.warning(
                self,
                "URL da candidatura",
                "Informe primeiro o link da vaga do LinkedIn.",
            )
            return
        if "linkedin.com" not in job_url.lower():
            QMessageBox.information(
                self,
                "URL da candidatura",
                "A detecção automática está disponível para vagas do LinkedIn.",
            )
            return
        self.detect_application_url_button.setEnabled(False)
        self.import_status_label.setText("Localizando link Candidatar-se...")
        resolver = self._application_url_resolver
        self._application_url_executor.execute_with_context(
            lambda emit, _token: resolver.resolve_linkedin_application_url(
                job_url,
                progress=emit,
            )
        )

    def _on_application_url_progress(self, payload: object) -> None:
        if isinstance(payload, tuple) and len(payload) == 2:
            _value, message = payload
            self.import_status_label.setText(str(message))

    def _on_application_url_resolved(self, result: object) -> None:
        resolution = (
            result
            if isinstance(result, LinkedInApplicationResolution)
            else LinkedInApplicationResolution(url=str(result or "").strip())
        )
        if resolution.accepting_applications is False:
            self.import_status_label.setText("Não aceita mais candidaturas")
            confirmation = QMessageBox.question(
                self,
                "Não aceita mais candidaturas",
                "Não foi localizado o botão Candidatar-se nem Candidatura "
                "simplificada. A vaga não aceita mais candidaturas.\n\n"
                "Deseja excluir esta vaga do aplicativo?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if confirmation == QMessageBox.Yes:
                self._delete_current_closed_job()
            return

        application_url = resolution.url.strip()
        if application_url and self._same_job_and_application_url(
            self.url_input.text(),
            application_url,
        ):
            self.import_status_label.setText("Não aceita mais candidaturas")
            confirmation = QMessageBox.question(
                self,
                "Não aceita mais candidaturas",
                "O Link da vaga e a URL da candidatura são iguais. "
                "Esta vaga não aceita mais candidaturas.\n\n"
                "Deseja excluir esta vaga do aplicativo?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if confirmation == QMessageBox.Yes:
                self._delete_current_closed_job()
            return

        if application_url:
            self.application_url_input.setText(application_url)
            label = (
                "Candidatura simplificada localizada."
                if resolution.application_type == "easy_apply"
                else "Link Candidatar-se localizado."
            )
            self.import_status_label.setText(label)
            self._persist_application_url_if_possible(application_url)
            return

        if resolution.accepting_applications:
            self.import_status_label.setText(
                "Candidatar-se localizado, mas a URL não pôde ser determinada."
            )
            QMessageBox.warning(
                self,
                "URL da candidatura",
                "O botão Candidatar-se foi localizado, portanto a vaga aceita "
                "candidaturas, mas o LinkedIn não expôs a URL de destino. "
                "A vaga não será excluída.",
            )
            return

        if resolution.accepting_applications is None:
            self.import_status_label.setText(
                "Não foi possível confirmar a forma de candidatura."
            )
            QMessageBox.warning(
                self,
                "URL da candidatura",
                "Não foi possível localizar o botão Candidatar-se nem confirmar "
                "que a vaga esteja encerrada. A vaga não será excluída.",
            )
            return

        self.import_status_label.setText("Não aceita mais candidaturas")

    @staticmethod
    def _same_job_and_application_url(job_url: str, application_url: str) -> bool:
        return job_url.strip().rstrip("/") == application_url.strip().rstrip("/")

    def _delete_current_closed_job(self) -> None:
        job_url = self.url_input.text().strip()
        linkedin_job_id = self._closed_jobs_registry.job_id_from_url(job_url)
        if linkedin_job_id:
            self._closed_jobs_registry.mark_closed(linkedin_job_id)

        job = None
        if self.current_job_id is not None:
            job = self.job_service.get_job(self.current_job_id)
        if job is None and job_url:
            job = self.job_service.get_job_by_url(job_url)
        if job is None and linkedin_job_id:
            job = self.job_service.get_job_by_linkedin_job_id(linkedin_job_id)

        if job is not None and job.id is not None:
            self.job_service.delete_job(int(job.id), delete_linked=True)

        self.current_job_id = None
        self._clear_form()
        self._load_jobs()
        self.import_status_label.setText(
            "Vaga encerrada: excluída e bloqueada para novas importações."
        )
        QMessageBox.information(
            self,
            "Vaga excluída",
            "A vaga foi excluída do aplicativo e não será importada novamente.",
        )

    def _persist_application_url_if_possible(self, application_url: str) -> None:
        if self.current_job_id is None:
            return
        job = self.job_service.get_job(self.current_job_id)
        if job is None:
            return
        # Reuse the regular form-save path so the detected URL is persisted
        # together with the values currently displayed to the user.
        self._save_job(clear_after=False, show_success=False)

    def _on_application_url_resolution_failed(self, error: object) -> None:
        self.import_status_label.setText("Falha ao localizar link externo.")
        QMessageBox.warning(self, "URL da candidatura", str(error))

    def _on_application_url_resolution_finished(self) -> None:
        self.detect_application_url_button.setEnabled(True)

    def _on_linkedin_import_failed(self, error: object) -> None:
        self.import_status_label.setText("Falha na importação.")
        QMessageBox.critical(self, "Não foi possível importar", str(error))

    def _on_linkedin_import_finished(self) -> None:
        self.import_linkedin_button.setEnabled(True)


    def _research_salary(self) -> None:
        if self._salary_research_service is None:
            QMessageBox.warning(
                self,
                "Pesquisa salarial",
                "O serviço de pesquisa salarial não está disponível.",
            )
            return

        request = SalaryResearchRequest(
            title=self.title_input.text().strip(),
            location=self.location_input.text().strip(),
            work_model=self.work_model_combo.currentText().strip(),
            employment_type=self.employment_type_combo.currentText().strip(),
        )
        try:
            SalaryResearchService._validate_request(request)
        except ValueError as exc:
            QMessageBox.warning(self, "Pesquisa salarial", str(exc))
            return

        if self._salary_research_executor.is_running:
            QMessageBox.information(
                self,
                "Pesquisa salarial",
                "A pesquisa salarial já está em andamento.",
            )
            return

        self.salary_research_button.setEnabled(False)
        self.salary_research_button.setText("Pesquisando salários...")
        service = self._salary_research_service
        self._salary_research_executor.execute(
            lambda: service.research(request, force_refresh=True),
            timeout_ms=120_000,
        )

    def _on_salary_research_succeeded(self, result: object) -> None:
        if not isinstance(result, SalaryResearchResult):
            QMessageBox.warning(
                self,
                "Pesquisa salarial",
                "A pesquisa retornou um resultado inválido.",
            )
            return

        currency_index = self.currency_input.findText(result.currency)
        if currency_index >= 0:
            self.currency_input.setCurrentIndex(currency_index)
        self.salary_max_input.setValue(result.salary_max)
        self._update_currency_symbol()
        if self._save_job(clear_after=False, show_success=False):
            self.import_status_label.setText(
                "Remuneração ideal atualizada pela IA e vaga salva."
            )
        else:
            self.import_status_label.setText(
                "Remuneração ideal preenchida, mas a vaga não pôde ser salva."
            )

    def _on_salary_research_failed(self, error: object) -> None:
        QMessageBox.critical(
            self,
            "Não foi possível pesquisar salários",
            str(error),
        )

    def _on_salary_research_finished(self) -> None:
        self.salary_research_button.setEnabled(True)
        self.salary_research_button.setText("Pesquisar média salarial com IA")

    def _save_current_job(self) -> None:
        """Salva e permanece no registro atual, confirmando ao usuário."""
        if self._save_job(clear_after=False, show_success=False):
            QMessageBox.information(
                self,
                "Registro salvo",
                "O registro foi salvo",
            )

    def _save_job(self, *, clear_after: bool = True, show_success: bool = True) -> bool:
        try:
            company_id = self.company_combo.currentData()
            title = self.title_input.text().strip()
            location = self.location_input.text().strip()
            work_model = self.work_model_combo.currentText()
            employment_type = self.employment_type_combo.currentText()
            salary_min = self._parse_offered_remuneration()
            salary_max = self.salary_max_input.value()
            currency = self.currency_input.currentText()
            status = self.status_combo.currentText()
            source = self.source_input.text().strip()
            job_url = self.url_input.text().strip()
            application_url = self.application_url_input.text().strip()
            recruiter = self.recruiter_input.text().strip()
            recruiter_email = self.recruiter_email_input.text().strip()
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
            notes = self._notes_with_benefits(
                self.notes_input.toPlainText().strip(),
                self.benefits_input.toPlainText().strip(),
            )

            if company_id in (None, ""):
                raise ValueError("Selecione uma empresa.")
            company_id_value = int(company_id)

            if self.current_job_id is None:
                saved_job = self.job_service.create_job(
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
                    application_url=application_url,
                    recruiter=recruiter,
                    recruiter_email=recruiter_email,
                    application_deadline=deadline,
                    application_date=application_date,
                    priority=priority,
                    notes=notes,
                )
            else:
                saved_job = self.job_service.update_job(
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
                    application_url=application_url,
                    recruiter=recruiter,
                    recruiter_email=recruiter_email,
                    application_deadline=deadline,
                    application_date=application_date,
                    priority=priority,
                    notes=notes,
                )

            if saved_job is None:
                raise ValueError("A vaga não foi encontrada para atualização.")
            self.current_job_id = int(saved_job.id)
            selected_job_id = self.current_job_id
            self._load_jobs()
            if clear_after:
                self._clear_form()
            else:
                self._select_job_row_by_id(selected_job_id)
                if show_success:
                    self.import_status_label.setText("Vaga salva.")
            return True
        except ValueError as exc:
            QMessageBox.warning(self, "Dados inválidos", str(exc))
            return False
        except Exception as exc:  # pragma: no cover - defensive UI handling
            QMessageBox.critical(self, "Erro", str(exc))
            return False

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
        except Exception as exc:
            if not _is_integrity_error(exc):
                QMessageBox.critical(
                    self,
                    "Não foi possível excluir",
                    f"Ocorreu um erro ao excluir a vaga:\n{exc}",
                )
                return
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

        self.work_model_combo.setCurrentText(job.work_model or "Presencial")

        self.employment_type_combo.setCurrentText(job.employment_type or "")

        self._set_offered_remuneration(float(job.salary_min) if job.salary_min is not None else None)

        self.salary_max_input.setValue(float(job.salary_max or 0))

        index = self.currency_input.findText(job.currency or "R$")

        if index >= 0:
            self.currency_input.setCurrentIndex(index)

        self._update_currency_symbol()

        self.status_combo.setCurrentText(job.status or "Nova")

        self.source_input.setText(job.source or "")

        self.url_input.setText(job.job_url or "")
        self.application_url_input.setText(getattr(job, "application_url", "") or "")

        self.recruiter_input.setText(job.recruiter or "")
        self.recruiter_email_input.setText(
            getattr(job, "recruiter_email", "") or ""
        )

        if job.application_deadline:
            self.deadline_input.setDate(job.application_deadline)

        if job.application_date:
            self.application_date_input.setDate(job.application_date)

        self.priority_input.setValue(job.priority or 3)

        stored_notes = job.notes or ""
        self.benefits_input.setPlainText(self._extract_benefits_marker(stored_notes))
        self.notes_input.setPlainText(self._strip_benefits_marker(stored_notes))

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

    def _select_job_row_by_id(self, job_id: int | None) -> None:
        """Mantém a seleção da tabela no registro atualmente editado."""
        if job_id is None:
            return
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None and item.text() == str(job_id):
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                return

    def _clear_form(self) -> None:
        """Limpa o formulário e prepara para um novo cadastro."""
        self.current_job_id = None
        self.company_combo.setCurrentIndex(0)
        self.title_input.clear()
        self.location_input.clear()
        self.work_model_combo.setCurrentText("Presencial")
        self.employment_type_combo.setCurrentIndex(0)
        self.salary_min_input.setValue(0.00)
        self.salary_max_input.setValue(0.00)
        self.currency_input.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.source_input.clear()
        self.url_input.clear()
        self.application_url_input.clear()
        self.import_status_label.clear()
        self.recruiter_input.clear()
        self.recruiter_email_input.clear()
        # Reinicia as datas para a data atual
        self.deadline_input.setDate(QDate.currentDate())
        self.application_date_input.setDate(QDate.currentDate())
        self.priority_input.setValue(3)
        self.benefits_input.clear()
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

    _BENEFITS_START = "[BENEFICIOS]"
    _BENEFITS_END = "[/BENEFICIOS]"

    def _set_offered_remuneration(self, value: float | None) -> None:
        self.salary_min_input.setValue(float(value or 0.0))

    def _parse_offered_remuneration(self) -> float | None:
        value = float(self.salary_min_input.value())
        return value if value > 0 else None

    @classmethod
    def _notes_with_benefits(cls, notes: str, benefits: str) -> str:
        clean_notes = cls._strip_benefits_marker(notes).strip()
        clean_benefits = benefits.strip()
        if not clean_benefits:
            return clean_notes
        marker = f"{cls._BENEFITS_START}\n{clean_benefits}\n{cls._BENEFITS_END}"
        return f"{clean_notes}\n\n{marker}".strip()

    @classmethod
    def _extract_benefits_marker(cls, notes: str) -> str:
        start = notes.find(cls._BENEFITS_START)
        end = notes.find(cls._BENEFITS_END)
        if start < 0 or end < 0 or end <= start:
            return ""
        start += len(cls._BENEFITS_START)
        return notes[start:end].strip()

    @classmethod
    def _strip_benefits_marker(cls, notes: str) -> str:
        start = notes.find(cls._BENEFITS_START)
        end = notes.find(cls._BENEFITS_END)
        if start < 0 or end < 0 or end <= start:
            return notes.strip()
        end += len(cls._BENEFITS_END)
        return f"{notes[:start]}{notes[end:]}".strip()

    @staticmethod
    def _format_benefits(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (list, tuple, set)):
            return "\n".join(str(item).strip() for item in value if str(item).strip())
        return str(value).strip()

    def _parse_optional_number(self, value: str) -> float | None:
        if not value.strip():
            return None
        return float(value)


def _is_integrity_error(exc: BaseException) -> bool:
    current: BaseException | None = exc
    while current is not None:
        if current.__class__.__name__ == "IntegrityError":
            return True
        current = current.__cause__ or current.__context__
    return False
