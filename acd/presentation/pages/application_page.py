from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Protocol

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.candidate_decision_panel import CandidateDecisionPanel
from acd.presentation.effective_application_resume_preview_panel import (
    EffectiveApplicationResumePreviewPanel,
)
from acd.presentation.long_running_task_executor import LongRunningTaskExecutor
from acd.presentation.models.candidate_decision_action import CandidateDecisionAction
from acd.presentation.models.effective_application_resume_view_state import (
    EffectiveApplicationResumeViewState,
)
from acd.presentation.models.effective_structured_resume_docx_export_view_state import (
    EffectiveStructuredResumeDocxExportViewState,
)
from acd.presentation.models.optimized_resume_evaluation_view_state import (
    OptimizedResumeEvaluationViewState,
)
from acd.presentation.models.resume_adoption_view_state import ResumeAdoptionViewState
from acd.presentation.models.resume_optimization_view_state import ResumeOptimizationViewState
from acd.presentation.models.resume_version_review_view_state import ResumeVersionReviewViewState
from acd.presentation.models.structured_resume_generation_view_state import (
    StructuredResumeGenerationViewState,
)
from acd.presentation.models.structured_resume_quality_validation_view_state import (
    StructuredResumeQualityValidationViewState,
)
from acd.presentation.pages.base_page import BasePage
from acd.presentation.pages.candidate_decision_view_model import CandidateDecisionViewModel
from acd.presentation.pages.effective_application_resume_view_model import (
    EffectiveApplicationResumeViewModel,
)
from acd.presentation.pages.effective_structured_resume_docx_export_view_model import (
    EffectiveStructuredResumeDocxExportViewModel,
)
from acd.presentation.pages.optimized_resume_evaluation_view_model import (
    OptimizedResumeEvaluationViewModel,
)
from acd.presentation.pages.resume_adoption_view_model import ResumeAdoptionViewModel
from acd.presentation.pages.resume_optimization_view_model import ResumeOptimizationViewModel
from acd.presentation.pages.resume_version_review_view_model import ResumeVersionReviewViewModel
from acd.presentation.pages.structured_resume_generation_view_model import (
    StructuredResumeGenerationViewModel,
)
from acd.presentation.pages.structured_resume_quality_validation_view_model import (
    StructuredResumeQualityValidationViewModel,
)
from acd.presentation.resume_version_review_panel import ResumeVersionReviewPanel


class _ApplicationData(Protocol):
    def list_applications(self) -> list[object]: ...
    def search_applications(self, query: str) -> list[object]: ...
    def filter_applications(self, **filters: object) -> list[object]: ...
    def get_application(self, application_id: int) -> object | None: ...
    def create_application(self, **data: object) -> object: ...
    def update_application(self, application_id: int, **data: object) -> object | None: ...
    def delete_application(self, application_id: int, *, delete_linked: bool = False) -> bool: ...


class _CompanyData(Protocol):
    def list_companies(self) -> list[object]: ...


class _JobData(Protocol):
    def filter_jobs(self, **filters: object) -> list[object]: ...


class _EmptyApplicationData:
    """In-memory boundary used only by isolated Presentation tests."""

    def list_companies(self) -> list[object]:
        return []

    def filter_jobs(self, **_: object) -> list[object]:
        return []

    def list_applications(self) -> list[object]:
        return []

    def get_application(self, _: int) -> object | None:
        return None

    def search_applications(self, _: str) -> list[object]:
        return []

    def filter_applications(self, **_: object) -> list[object]:
        return []


class ApplicationPage(BasePage):
    """Página de cadastro e gerenciamento de candidaturas."""

    def __init__(
        self,
        candidate_decision_view_model: CandidateDecisionViewModel | None = None,
        on_candidate_decision_action: Callable[[str], None] | None = None,
        resume_optimization_view_model: ResumeOptimizationViewModel | None = None,
        resume_version_review_view_model: ResumeVersionReviewViewModel | None = None,
        optimized_resume_evaluation_view_model: OptimizedResumeEvaluationViewModel | None = None,
        resume_adoption_view_model: ResumeAdoptionViewModel | None = None,
        effective_application_resume_view_model: EffectiveApplicationResumeViewModel | None = None,
        structured_resume_generation_view_model: StructuredResumeGenerationViewModel | None = None,
        effective_structured_resume_docx_export_view_model: EffectiveStructuredResumeDocxExportViewModel | None = None,
        structured_resume_quality_validation_view_model: StructuredResumeQualityValidationViewModel | None = None,
        application_service: _ApplicationData | None = None,
        company_service: _CompanyData | None = None,
        job_service: _JobData | None = None,
    ) -> None:
        super().__init__("Candidaturas")

        self._candidate_decision_view_model = candidate_decision_view_model
        self._on_candidate_decision_action_callback = on_candidate_decision_action
        self._resume_optimization_view_model = resume_optimization_view_model
        self._resume_version_review_view_model = resume_version_review_view_model
        self._optimized_resume_evaluation_view_model = optimized_resume_evaluation_view_model
        self._resume_adoption_view_model = resume_adoption_view_model
        self._effective_application_resume_view_model = effective_application_resume_view_model
        self._structured_resume_generation_view_model = structured_resume_generation_view_model
        self._effective_structured_resume_docx_export_view_model = effective_structured_resume_docx_export_view_model
        self._structured_resume_quality_validation_view_model = structured_resume_quality_validation_view_model
        self._structured_resume_quality_validation_application_id: int | None = None
        self._effective_resume_state: EffectiveApplicationResumeViewState | None = None
        self._resume_review_state: ResumeVersionReviewViewState | None = None
        self._resume_optimization_executor = LongRunningTaskExecutor(self)
        self._resume_optimization_executor.started.connect(self._on_long_running_task_started)
        self._resume_optimization_executor.succeeded.connect(self._on_long_running_task_succeeded)
        self._resume_optimization_executor.failed.connect(self._on_long_running_task_failed)
        self._resume_optimization_executor.finished.connect(self._on_long_running_task_finished)
        self._active_long_running_task: str | None = None
        self._optimized_evaluation_request: tuple[int, int] | None = None
        self._structured_resume_generation_application_id: int | None = None
        self._effective_resume_docx_export_application_id: int | None = None
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)
        # The desktop root always injects real dependencies. The empty boundary
        # permits isolated ViewModel tests without reintroducing service creation.
        self.application_service = application_service or _EmptyApplicationData()
        self.company_service = company_service or _EmptyApplicationData()
        self.job_service = job_service or _EmptyApplicationData()
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
        self.optimize_resume_button = QPushButton("Otimizar currículo")
        self.generate_structured_resume_button = QPushButton("Gerar versão estruturada")
        self.export_effective_resume_docx_button = QPushButton("Exportar currículo em DOCX")
        self.export_effective_resume_docx_button.setToolTip("Exporta o currículo efetivo atual para um arquivo DOCX.")
        self.export_effective_resume_docx_button.setEnabled(False)
        self.validate_structured_resume_quality_button = QPushButton("Validar qualidade do currículo")
        self.validate_structured_resume_quality_button.setToolTip("Verifica integridade, completude, consistência e exportabilidade do currículo efetivo.")
        self.validate_structured_resume_quality_button.setEnabled(False)
        self.structured_resume_quality_label = QLabel()
        self.structured_resume_quality_issues = QTextEdit()
        self.structured_resume_quality_issues.setReadOnly(True)
        self.generate_structured_resume_button.setEnabled(False)
        self.optimize_resume_button.setEnabled(False)
        self.optimization_status_label = QLabel()
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Empresa", "Vaga", "Status", "Aplicação", "Follow-up"]
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
        self.candidate_decision_panel = CandidateDecisionPanel()
        self.candidate_decision_panel.action_requested.connect(self._on_candidate_decision_action)
        self.resume_version_review_panel = ResumeVersionReviewPanel()
        self.effective_application_resume_preview_panel = EffectiveApplicationResumePreviewPanel()
        self.resume_version_review_panel.version_selected.connect(
            self._on_resume_version_selected
        )
        self.resume_version_review_panel.evaluation_requested.connect(
            self._evaluate_optimized_resume
        )
        self.resume_version_review_panel.adopt_version_requested.connect(self._adopt_resume_version)
        self.resume_version_review_panel.use_original_requested.connect(self._use_original_resume)
        self.resume_version_review_panel.set_evaluation_available(
            self._optimized_resume_evaluation_view_model is not None
        )

        self._setup_controls()
        self.company_combo.currentIndexChanged.connect(self._load_jobs)
        self._load_companies()
        self._load_applications()

    def refresh_reference_data(self) -> None:
        """Atualiza empresas, vagas e candidaturas ao entrar na página."""
        selected_company = self.company_combo.currentData()
        self._load_companies()
        if selected_company not in (None, ""):
            index = self.company_combo.findData(selected_company)
            if index >= 0:
                self.company_combo.setCurrentIndex(index)
        self._load_jobs()
        self._load_applications()

    def _setup_controls(self) -> None:
        for date_input in (
            self.application_date_input,
            self.next_follow_up_input,
            self.response_date_input,
            self.interview_date_input,
        ):
            date_input.setCalendarPopup(True)
            date_input.setDisplayFormat("dd/MM/yyyy")

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
        actions.addWidget(self.optimize_resume_button)
        actions.addWidget(self.generate_structured_resume_button)
        actions.addWidget(self.export_effective_resume_docx_button)
        actions.addWidget(self.validate_structured_resume_quality_button)
        actions.addStretch()
        self.save_button.clicked.connect(self._save_application)
        self.delete_button.clicked.connect(self._delete_application)
        self.optimize_resume_button.clicked.connect(self._optimize_resume)
        self.generate_structured_resume_button.clicked.connect(self._generate_structured_resume_version)
        self.export_effective_resume_docx_button.clicked.connect(self._export_effective_resume_docx)
        self.validate_structured_resume_quality_button.clicked.connect(self._validate_structured_resume_quality)

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

        self.content_layout.addLayout(form)
        self.content_layout.addWidget(self.structured_resume_quality_label)
        self.content_layout.addWidget(self.structured_resume_quality_issues)
        self.content_layout.addLayout(actions)
        self.content_layout.addLayout(search_layout)
        self.content_layout.addLayout(filter_layout)
        self.content_layout.addWidget(self.table)
        self.content_layout.addWidget(self.candidate_decision_panel)
        self.content_layout.addWidget(self.resume_version_review_panel)
        self.content_layout.addWidget(self.effective_application_resume_preview_panel)
        self.content_layout.addWidget(self.optimization_status_label)

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

            if company_id in (None, ""):
                raise ValueError("Selecione uma empresa.")
            if job_id in (None, ""):
                raise ValueError("Selecione uma vaga.")
            company_id_value = int(company_id)
            job_id_value = int(job_id)

            if self.current_application_id is None:
                self.application_service.create_application(
                    job_id=job_id_value,
                    company_id=company_id_value,
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
                    job_id=job_id_value,
                    company_id=company_id_value,
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
            QMessageBox.information(
                self,
                "Candidatura",
                "Selecione uma candidatura para excluir.",
            )
            return
        confirmation = QMessageBox.question(
            self,
            "Confirmar exclusão",
            "Deseja excluir esta candidatura?",
        )
        if confirmation != QMessageBox.Yes:
            return
        try:
            deleted = self.application_service.delete_application(
                self.current_application_id
            )
            if not deleted:
                QMessageBox.warning(
                    self,
                    "Candidatura",
                    "A candidatura não pôde ser excluída.",
                )
                return
            self._clear_form()
            self._load_applications()
        except Exception as exc:  # pragma: no cover - defensive UI handling
            if not self._is_integrity_error(exc):
                QMessageBox.critical(
                    self,
                    "Não foi possível excluir",
                    f"A candidatura possui registros vinculados ou ocorreu um erro:\n{exc}",
                )
                return

            cascade_confirmation = QMessageBox.question(
                self,
                "Registros vinculados",
                "Esta candidatura possui entrevistas, eventos e demais registros vinculados.\n\n"
                "Deseja excluir também todos os registros vinculados? "
                "Esta operação não poderá ser desfeita.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if cascade_confirmation != QMessageBox.Yes:
                return
            try:
                deleted = self.application_service.delete_application(
                    self.current_application_id,
                    delete_linked=True,
                )
                if not deleted:
                    QMessageBox.warning(
                        self,
                        "Candidatura",
                        "O registro não pôde ser excluído.",
                    )
                    return
                self._clear_form()
                self._load_applications()
            except Exception:
                QMessageBox.critical(
                    self,
                    "Não foi possível excluir",
                    "Não foi possível excluir o registro e seus vínculos.",
                )

    @staticmethod
    def _is_integrity_error(error: Exception) -> bool:
        error_type = type(error)
        return error_type.__name__ == "IntegrityError" and error_type.__module__.startswith(
            "sqlalchemy"
        )

    def _on_row_selected(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.current_application_id = None
            self.optimize_resume_button.setEnabled(False)
            self.generate_structured_resume_button.setEnabled(False)
            self.candidate_decision_panel.show_empty_state()
            self.candidate_decision_panel.render_actions(())
            self.resume_version_review_panel.show_empty_state()
            self.effective_application_resume_preview_panel.show_empty_state()
            return
        row = selected_rows[0].row()
        self.current_application_id = int(self.table.item(row, 0).text())
        self.optimize_resume_button.setEnabled(
            self._resume_optimization_view_model is not None
            and not self._resume_optimization_executor.is_running
        )
        self.generate_structured_resume_button.setEnabled(
            self._structured_resume_generation_view_model is not None
            and not self._resume_optimization_executor.is_running
        )
        self.export_effective_resume_docx_button.setEnabled(
            self._effective_structured_resume_docx_export_view_model is not None
            and not self._resume_optimization_executor.is_running
        )
        self.validate_structured_resume_quality_button.setEnabled(
            self._structured_resume_quality_validation_view_model is not None
            and not self._resume_optimization_executor.is_running
        )
        application = self.application_service.get_application(
            self.current_application_id
        )
        if application is not None:
            company_index = self.company_combo.findData(application.company_id)
            if company_index >= 0:
                self.company_combo.setCurrentIndex(company_index)
            self._load_jobs()
            job_index = self.job_combo.findData(application.job_id)
            if job_index >= 0:
                self.job_combo.setCurrentIndex(job_index)
            self.status_combo.setCurrentText(application.status or "")
            for widget, value in (
                (self.application_date_input, application.application_date),
                (self.next_follow_up_input, application.next_follow_up),
                (self.response_date_input, application.response_date),
                (self.interview_date_input, application.interview_date),
            ):
                if value is not None:
                    widget.setDate(QDate(value.year, value.month, value.day))
            self.salary_expected_input.setText(
                "" if application.salary_expected is None else str(application.salary_expected)
            )
            self.salary_offered_input.setText(
                "" if application.salary_offered is None else str(application.salary_offered)
            )
            self.channel_input.setText(application.application_channel or "")
            self.recruiter_name_input.setText(application.recruiter_name or "")
            self.recruiter_email_input.setText(application.recruiter_email or "")
            self.recruiter_phone_input.setText(application.recruiter_phone or "")
            self.feedback_input.setPlainText(application.feedback or "")
            self.notes_input.setPlainText(application.notes or "")

        self._load_candidate_decision()
        self._load_resume_version_review()
        self._load_effective_application_resume()

    def _load_candidate_decision(self) -> None:
        if self.current_application_id is None:
            self.candidate_decision_panel.show_empty_state()
            self.candidate_decision_panel.render_actions(())
            return
        if self._candidate_decision_view_model is None:
            self.candidate_decision_panel.show_empty_state()
            self.candidate_decision_panel.render_actions(())
            return
        self.candidate_decision_panel.render(
            self._candidate_decision_view_model.load(self.current_application_id)
        )
        self.candidate_decision_panel.render_actions(self._candidate_decision_actions())

    def _load_resume_version_review(self) -> None:
        if (
            self.current_application_id is None
            or self._resume_version_review_view_model is None
        ):
            self.resume_version_review_panel.show_empty_state()
            return
        self._resume_review_state = self._resume_version_review_view_model.load(
            self.current_application_id
        )
        self.resume_version_review_panel.render(self._resume_review_state)

    def _on_resume_version_selected(self, version_id: int) -> None:
        if (
            self.current_application_id is None
            or self._resume_version_review_view_model is None
        ):
            return
        self._resume_review_state = self._resume_version_review_view_model.select_version(
            self.current_application_id,
            version_id,
        )
        self.resume_version_review_panel.render(self._resume_review_state)

    def _load_effective_application_resume(self) -> None:
        """Render the persisted source independently from the viewed version."""
        if self.current_application_id is None or self._effective_application_resume_view_model is None:
            self._effective_resume_state = None
            self.effective_application_resume_preview_panel.show_empty_state()
            return
        state = self._effective_application_resume_view_model.load(self.current_application_id)
        if state.application_id != self.current_application_id:
            return
        self._effective_resume_state = state
        self.effective_application_resume_preview_panel.render(state)

    def _adopt_resume_version(self, version_id: int) -> None:
        if self.current_application_id is None or self._resume_adoption_view_model is None:
            return
        self.resume_version_review_panel.set_adoption_running(True)
        try:
            state = self._resume_adoption_view_model.adopt(self.current_application_id, version_id)
            self._render_adoption_result(state)
        except Exception:
            self.resume_version_review_panel.set_adoption_running(False)
            self.resume_version_review_panel.adoption_message_label.setText(
                "Não foi possível atualizar o currículo."
            )

    def _use_original_resume(self) -> None:
        if self.current_application_id is None or self._resume_adoption_view_model is None:
            return
        self.resume_version_review_panel.set_adoption_running(True)
        try:
            state = self._resume_adoption_view_model.use_original(self.current_application_id)
            self._render_adoption_result(state)
        except Exception:
            self.resume_version_review_panel.set_adoption_running(False)
            self.resume_version_review_panel.adoption_message_label.setText(
                "Não foi possível atualizar o currículo."
            )

    def _render_adoption_result(self, state: ResumeAdoptionViewState) -> None:
        if self._resume_review_state is None or state.application_id != self.current_application_id:
            return
        if state.status in {"success", "already_selected"}:
            self._resume_review_state = replace(
                self._resume_review_state,
                resume_source=state.resume_source,
                selected_resume_version_id=state.selected_resume_version_id,
            )
        self.resume_version_review_panel.render_adoption(state, self._resume_review_state)
        if state.status in {"success", "already_selected"}:
            self._load_effective_application_resume()

    def _evaluate_optimized_resume(self, version_id: int) -> None:
        if (
            self.current_application_id is None
            or self._optimized_resume_evaluation_view_model is None
            or self._resume_optimization_executor.is_running
        ):
            return
        application_id = self.current_application_id
        self._optimized_evaluation_request = (application_id, version_id)
        self._active_long_running_task = "optimized_evaluation"
        self._resume_optimization_executor.execute(
            lambda: self._optimized_resume_evaluation_view_model.evaluate(
                application_id,
                version_id,
            )
        )

    def _on_optimized_evaluation_started(self) -> None:
        self.resume_version_review_panel.set_evaluation_running(True)

    def _on_optimized_evaluation_succeeded(
        self,
        state: OptimizedResumeEvaluationViewState,
    ) -> None:
        if (
            state.application_id != self.current_application_id
            or state.resume_version_id != self.resume_version_review_panel.selected_version_id
        ):
            return
        self.resume_version_review_panel.render_evaluation(state)

    def _on_optimized_evaluation_failed(self, error: Exception) -> None:
        request = self._optimized_evaluation_request
        if request is None or request[0] != self.current_application_id:
            return
        self.resume_version_review_panel.evaluation_label.setText(
            "Não foi possível avaliar a versão selecionada."
        )

    def _on_optimized_evaluation_finished(self) -> None:
        self._optimized_evaluation_request = None
        self.resume_version_review_panel.set_evaluation_running(False)

    def _on_long_running_task_started(self) -> None:
        if self._active_long_running_task == "optimized_evaluation":
            self._on_optimized_evaluation_started()
        elif self._active_long_running_task == "structured_resume_generation":
            self.generate_structured_resume_button.setEnabled(False)
            self.optimize_resume_button.setEnabled(False)
            self.optimization_status_label.setText("Gerando versão estruturada...")
        elif self._active_long_running_task == "effective_resume_docx_export":
            self.export_effective_resume_docx_button.setEnabled(False)
            self.export_effective_resume_docx_button.setText("Exportando...")
            self.optimize_resume_button.setEnabled(False)
            self.generate_structured_resume_button.setEnabled(False)
        else:
            self._on_optimization_started()

    def _on_long_running_task_succeeded(self, state: object) -> None:
        if self._active_long_running_task == "optimized_evaluation":
            self._on_optimized_evaluation_succeeded(state)  # type: ignore[arg-type]
        elif self._active_long_running_task == "structured_resume_generation":
            self._on_structured_resume_generation_succeeded(state)
        elif self._active_long_running_task == "effective_resume_docx_export":
            self._on_effective_resume_docx_export_succeeded(state)
        elif self._active_long_running_task == "structured_resume_quality_validation":
            self._on_structured_resume_quality_validation_succeeded(state)
        else:
            self._on_optimization_succeeded(state)  # type: ignore[arg-type]

    def _on_long_running_task_failed(self, error: Exception) -> None:
        if self._active_long_running_task == "optimized_evaluation":
            self._on_optimized_evaluation_failed(error)
        elif self._active_long_running_task == "structured_resume_generation":
            self._on_structured_resume_generation_failed(error)
        elif self._active_long_running_task == "effective_resume_docx_export":
            self._on_effective_resume_docx_export_failed(error)
        elif self._active_long_running_task == "structured_resume_quality_validation":
            if self._structured_resume_quality_validation_application_id == self.current_application_id:
                self.structured_resume_quality_label.setText("Não foi possível validar a qualidade do currículo.")
        else:
            self._on_optimization_failed(error)

    def _on_structured_resume_generation_succeeded(self, state: object) -> None:
        if not isinstance(state, StructuredResumeGenerationViewState):
            if self.current_application_id is not None:
                self.optimization_status_label.setText(
                    "Não foi possível gerar a nova versão estruturada."
                )
            return
        if getattr(state, "application_id", None) != self.current_application_id:
            return
        self.optimization_status_label.setText(f"{state.title}: {state.message}")
        if getattr(state, "is_success", False):
            try:
                self._load_resume_version_review()
            except Exception:
                self.optimization_status_label.setText(
                    "Versão estruturada gerada, mas não foi possível atualizar o histórico."
                )

    def _on_structured_resume_generation_failed(self, error: Exception) -> None:
        if (
            self.current_application_id is None
            or self._structured_resume_generation_application_id != self.current_application_id
        ):
            return
        del error
        self.optimization_status_label.setText("Não foi possível gerar a nova versão estruturada.")

    def _on_long_running_task_finished(self) -> None:
        if self._active_long_running_task == "optimized_evaluation":
            self._on_optimized_evaluation_finished()
        else:
            self._on_optimization_finished()
        if self._active_long_running_task == "structured_resume_generation":
            self.generate_structured_resume_button.setEnabled(
                self.current_application_id is not None
                and self._structured_resume_generation_view_model is not None
            )
            self._structured_resume_generation_application_id = None
        if self._active_long_running_task == "effective_resume_docx_export":
            self.export_effective_resume_docx_button.setText("Exportar currículo em DOCX")
            self.export_effective_resume_docx_button.setEnabled(
                self.current_application_id is not None
                and self._effective_structured_resume_docx_export_view_model is not None
            )
            self._effective_resume_docx_export_application_id = None
        if self._active_long_running_task == "structured_resume_quality_validation":
            self.validate_structured_resume_quality_button.setText("Validar qualidade do currículo")
            self.validate_structured_resume_quality_button.setEnabled(
                self.current_application_id is not None
                and self._structured_resume_quality_validation_view_model is not None
            )
            self._structured_resume_quality_validation_application_id = None
        self._active_long_running_task = None

    def _on_candidate_decision_action(self, action_id: str) -> None:
        if self.current_application_id is None:
            return
        if self._on_candidate_decision_action_callback is not None:
            self._on_candidate_decision_action_callback(action_id)

    def _optimize_resume(self) -> None:
        if (
            self.current_application_id is None
            or self._resume_optimization_view_model is None
            or self._active_long_running_task is not None
        ):
            return
        application_id = self.current_application_id
        self._active_long_running_task = "optimization"
        self._resume_optimization_executor.execute(
            lambda: self._resume_optimization_view_model.optimize(application_id)
        )

    def _generate_structured_resume_version(self) -> None:
        if (
            self.current_application_id is None
            or self._structured_resume_generation_view_model is None
            or self._active_long_running_task is not None
        ):
            return
        application_id = self.current_application_id
        self._active_long_running_task = "structured_resume_generation"
        self._structured_resume_generation_application_id = application_id
        try:
            self._resume_optimization_executor.execute(
                lambda: self._structured_resume_generation_view_model.generate(application_id)
            )
        except Exception:
            self._on_structured_resume_generation_failed(RuntimeError())
            self._on_long_running_task_finished()

    def _export_effective_resume_docx(self) -> None:
        if (
            self.current_application_id is None
            or self._effective_structured_resume_docx_export_view_model is None
            or self._active_long_running_task is not None
        ):
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar currículo em DOCX",
            "Daniel_Freitas_Oliveira_Curriculo.docx",
            "Documentos do Word (*.docx)",
        )
        if not path:
            return
        destination = path if path.lower().endswith(".docx") else f"{path}.docx"
        application_id = self.current_application_id
        self._active_long_running_task = "effective_resume_docx_export"
        self._effective_resume_docx_export_application_id = application_id
        try:
            self._resume_optimization_executor.execute(
                lambda: self._effective_structured_resume_docx_export_view_model.export(
                    application_id, destination
                )
            )
        except Exception:
            self._on_effective_resume_docx_export_failed(RuntimeError())
            self._on_long_running_task_finished()

    def _validate_structured_resume_quality(self) -> None:
        if (
            self.current_application_id is None
            or self._structured_resume_quality_validation_view_model is None
            or self._active_long_running_task is not None
        ):
            return
        application_id = self.current_application_id
        self._active_long_running_task = "structured_resume_quality_validation"
        self._structured_resume_quality_validation_application_id = application_id
        self.validate_structured_resume_quality_button.setEnabled(False)
        self.validate_structured_resume_quality_button.setText("Validando...")
        try:
            self._resume_optimization_executor.execute(
                lambda: self._structured_resume_quality_validation_view_model.validate(application_id)
            )
        except Exception:
            self._on_long_running_task_finished()

    def _on_structured_resume_quality_validation_succeeded(self, state: object) -> None:
        if not isinstance(state, StructuredResumeQualityValidationViewState):
            return
        if state.application_id != self.current_application_id:
            return
        self.structured_resume_quality_label.setText(
            f"{state.message} {state.summary} Score: {state.score}. "
            f"Erros: {state.error_count}; Alertas: {state.warning_count}; Observações: {state.info_count}."
        )
        self.structured_resume_quality_issues.setPlainText("\n\n".join(
            f"[{issue.severity.value.upper()}] {issue.section} / {issue.field}\n"
            f"{issue.message}\nRecomendação: {issue.recommendation}"
            for issue in state.issues
        ))

    def _on_effective_resume_docx_export_succeeded(self, state: object) -> None:
        if not isinstance(state, EffectiveStructuredResumeDocxExportViewState):
            self._on_effective_resume_docx_export_failed(RuntimeError())
            return
        if state.application_id != self.current_application_id:
            return
        self.optimization_status_label.setText(state.message)

    def _on_effective_resume_docx_export_failed(self, error: Exception) -> None:
        del error
        if self._effective_resume_docx_export_application_id != self.current_application_id:
            return
        self.optimization_status_label.setText("Não foi possível exportar o currículo em DOCX.")

    def _on_optimization_started(self) -> None:
        self.optimize_resume_button.setEnabled(False)
        self.generate_structured_resume_button.setEnabled(False)
        self.optimization_status_label.setText("Otimizando currículo...")

    def _on_optimization_succeeded(self, state: ResumeOptimizationViewState) -> None:
        if state.application_id != self.current_application_id:
            return
        message = state.message if state.version is None else f"{state.message} Versão: {state.version}."
        self.optimization_status_label.setText(f"{state.title}: {message}")

    def _on_optimization_failed(self, error: Exception) -> None:
        self.optimization_status_label.setText(f"Não foi possível otimizar o currículo: {error}")

    def _on_optimization_finished(self) -> None:
        self.optimize_resume_button.setEnabled(
            self.current_application_id is not None and self._resume_optimization_view_model is not None
        )
        self.generate_structured_resume_button.setEnabled(
            self.current_application_id is not None
            and self._structured_resume_generation_view_model is not None
        )

    @staticmethod
    def _candidate_decision_actions() -> tuple[CandidateDecisionAction, ...]:
        return (
            CandidateDecisionAction(
                id="review_gaps",
                label="Revisar gaps",
                description="Abrir o planejamento de carreira e suas lacunas.",
                enabled=True,
            ),
            CandidateDecisionAction(
                id="prepare_curriculum",
                label="Preparar currículo",
                description="Abrir o gerenciamento de currículos existente.",
                enabled=True,
            ),
            CandidateDecisionAction(
                id="prepare_interview",
                label="Preparar entrevista",
                description="Abrir o gerenciamento de entrevistas existente.",
                enabled=True,
            ),
        )

    def _load_applications(self) -> None:
        applications = self.application_service.list_applications()
        self._render_applications(applications)

    def _filter_applications(self) -> None:
        status = self.filter_status_combo.currentText() or None
        company_id_data = self.filter_company_combo.currentData()
        company_id = (
            int(company_id_data)
            if company_id_data not in (None, "")
            else None
        )
        query = self.search_input.text().strip()

        if query:
            applications = self.application_service.search_applications(query)
        elif status or company_id is not None:
            applications = self.application_service.filter_applications(
                status=status,
                company_id=company_id,
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
        self.optimize_resume_button.setEnabled(False)
        self.generate_structured_resume_button.setEnabled(False)
        self.candidate_decision_panel.show_empty_state()
        self.candidate_decision_panel.render_actions(())
        self.resume_version_review_panel.show_empty_state()
        self.effective_application_resume_preview_panel.show_empty_state()
        self._resume_review_state = None
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
