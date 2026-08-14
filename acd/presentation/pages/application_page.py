from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Protocol

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.candidate_decision_panel import CandidateDecisionPanel
from acd.presentation.dialogs.applicant_profile_dialog import ApplicantProfileDialog
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
from acd.services.assisted_application_service import (
    AssistedApplicationResult,
    AssistedApplicationService,
)
from acd.services.ats_service import ATSService
from acd.services.resume_match_service import ResumeMatchResult


class _ApplicationData(Protocol):
    def list_applications(self) -> list[object]: ...
    def search_applications(self, query: str) -> list[object]: ...
    def filter_applications(self, **filters: object) -> list[object]: ...
    def get_application(self, application_id: int) -> object | None: ...
    def create_application(self, **data: object) -> object: ...
    def update_application(self, application_id: int, **data: object) -> object | None: ...
    def delete_application(self, application_id: int, *, delete_linked: bool = False) -> bool: ...


class _FollowUpData(Protocol):
    ACTION_TYPES: tuple[str, ...]
    INTERACTION_TYPES: tuple[str, ...]
    PRIORITIES: tuple[str, ...]

    def get_state(self, application_id: int) -> object: ...
    def get_timeline(self, application_id: int) -> tuple[object, ...]: ...
    def set_next_action(self, application_id: int, **data: object) -> object: ...
    def register_interaction(self, application_id: int, **data: object) -> object: ...
    def complete_follow_up(self, application_id: int, *, note: str = "") -> object: ...
    def postpone_follow_up(self, application_id: int, new_date: object, *, note: str = "") -> object: ...



class _CommunicationsData(Protocol):
    def sync_application(
        self,
        application_id: int,
        *,
        progress: Callable[[tuple[int, str]], None] | None = None,
    ) -> object: ...


class _CompanyData(Protocol):
    def list_companies(self) -> list[object]: ...


class _JobData(Protocol):
    def filter_jobs(self, **filters: object) -> list[object]: ...
    def get_job(self, job_id: int) -> object | None: ...



class _CurriculumData(Protocol):
    def associate_to_application(self, *, application_id: int, curriculum_id: int) -> object | None: ...
    def create_optimized_curriculum(
        self,
        *,
        source_curriculum_id: int,
        generated_version: str | None = None,
    ) -> object | None: ...
    def list_curricula(self) -> list[object]: ...
    def resolve_document_path(self, curriculum_id: int) -> str | None: ...


class _EmptyApplicationData:
    """In-memory boundary used only by isolated Presentation tests."""

    def list_companies(self) -> list[object]:
        return []

    def filter_jobs(self, **_: object) -> list[object]:
        return []

    def list_applications(self) -> list[object]:
        return []

    def list_curricula(self) -> list[object]:
        return []

    def get_application(self, _: int) -> object | None:
        return None

    def search_applications(self, _: str) -> list[object]:
        return []

    def filter_applications(self, **_: object) -> list[object]:
        return []



class _ResumeMatchData(Protocol):
    def analyze(self, *, application: object, curriculum: object) -> object: ...
    def get_cached(self, application_id: int, curriculum_id: int) -> object | None: ...


class _EmptyResumeMatchData:
    """Fallback boundary for isolated Presentation tests."""

    def analyze(self, *, application: object, curriculum: object) -> object:
        del application, curriculum
        raise RuntimeError("Serviço de aderência curricular não configurado.")

    def get_cached(self, application_id: int, curriculum_id: int) -> object | None:
        del application_id, curriculum_id
        return None


class ApplicationPage(BasePage):
    """Página de cadastro e gerenciamento de candidaturas."""

    def __init__(
        self,
        candidate_decision_view_model: CandidateDecisionViewModel | None = None,
        on_candidate_decision_action: Callable[[str], None] | None = None,
        on_optimized_curriculum_created: Callable[[int], None] | None = None,
        resume_optimization_view_model: ResumeOptimizationViewModel | None = None,
        resume_version_review_view_model: ResumeVersionReviewViewModel | None = None,
        optimized_resume_evaluation_view_model: OptimizedResumeEvaluationViewModel | None = None,
        resume_adoption_view_model: ResumeAdoptionViewModel | None = None,
        effective_application_resume_view_model: EffectiveApplicationResumeViewModel | None = None,
        structured_resume_generation_view_model: StructuredResumeGenerationViewModel | None = None,
        effective_structured_resume_docx_export_view_model: EffectiveStructuredResumeDocxExportViewModel | None = None,
        structured_resume_quality_validation_view_model: StructuredResumeQualityValidationViewModel | None = None,
        application_service: _ApplicationData | None = None,
        application_follow_up_service: _FollowUpData | None = None,
        communications_service: _CommunicationsData | None = None,
        company_service: _CompanyData | None = None,
        job_service: _JobData | None = None,
        curriculum_service: _CurriculumData | None = None,
        resume_match_service: _ResumeMatchData | None = None,
        ats_service: ATSService | None = None,
        assisted_application_service: AssistedApplicationService | None = None,
    ) -> None:
        super().__init__("Candidaturas")

        self._candidate_decision_view_model = candidate_decision_view_model
        self._on_candidate_decision_action_callback = on_candidate_decision_action
        self._on_optimized_curriculum_created_callback = on_optimized_curriculum_created
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
        progress_signal = getattr(self._resume_optimization_executor, "progress", None)
        if progress_signal is not None:
            progress_signal.connect(self._on_optimization_progress)
        self._optimization_progress_dialog: QProgressDialog | None = None
        self._active_long_running_task: str | None = None
        self._optimized_evaluation_request: tuple[int, int] | None = None
        self._structured_resume_generation_application_id: int | None = None
        self._effective_resume_docx_export_application_id: int | None = None
        self._optimization_source_curriculum_id: int | None = None
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)
        # The desktop root always injects real dependencies. The empty boundary
        # permits isolated ViewModel tests without reintroducing service creation.
        self.application_service = application_service or _EmptyApplicationData()
        self.application_follow_up_service = application_follow_up_service
        self.communications_service = communications_service
        self.company_service = company_service or _EmptyApplicationData()
        self.job_service = job_service or _EmptyApplicationData()
        self.curriculum_service = curriculum_service or _EmptyApplicationData()
        self.resume_match_service = resume_match_service or _EmptyResumeMatchData()
        self.ats_service = ats_service
        self.assisted_application_service = assisted_application_service
        self.current_application_id: int | None = None
        self._assisted_application_executor = LongRunningTaskExecutor(self)
        self._assisted_application_executor.succeeded.connect(self._on_assisted_application_succeeded)
        self._assisted_application_executor.failed.connect(self._on_assisted_application_failed)
        assisted_progress = getattr(self._assisted_application_executor, "progress", None)
        if assisted_progress is not None:
            assisted_progress.connect(self._on_assisted_application_progress)
        self._assisted_application_progress: QProgressDialog | None = None
        self._communications_executor = LongRunningTaskExecutor(self)
        self._communications_executor.succeeded.connect(self._on_outlook_sync_succeeded)
        self._communications_executor.failed.connect(self._on_outlook_sync_failed)
        self._communications_executor.finished.connect(self._on_outlook_sync_finished)

        communications_progress = getattr(self._communications_executor, "progress", None)
        if communications_progress is not None:
            communications_progress.connect(self._on_outlook_sync_progress)

        self._outlook_sync_progress: QProgressDialog | None = None

        self.company_combo = QComboBox()
        self.job_combo = QComboBox()
        self.status_combo = QComboBox()
        self.application_date_input = QDateEdit()
        self.next_follow_up_input = QDateEdit()
        self.next_action_combo = QComboBox()
        self.follow_up_priority_combo = QComboBox()
        self.follow_up_time_input = QLineEdit()
        self.follow_up_time_input.setPlaceholderText("HH:MM (opcional)")
        self.follow_up_note_input = QLineEdit()
        self.last_interaction_label = QLabel("Nenhuma interação registrada")
        self.register_interaction_button = QPushButton("Registrar interação")
        self.complete_follow_up_button = QPushButton("Concluir follow-up")
        self.postpone_follow_up_button = QPushButton("Adiar follow-up")
        self.timeline_button = QPushButton("Ver timeline")
        self.outlook_sync_button = QPushButton("Sincronizar Outlook Classic")
        self.outlook_sync_button.setEnabled(False)
        self.outlook_sync_button.setToolTip(
            "Lê respostas recebidas no Outlook Classic sem enviar, excluir, mover "
            "ou marcar mensagens como lidas."
        )
        self.response_date_input = QDateEdit()
        self.response_date_input.setReadOnly(True)
        self.interview_date_input = QDateEdit()
        self.salary_expected_input = QLineEdit()
        self.salary_offered_input = QLineEdit()
        self.channel_input = QLineEdit()
        self.recruiter_name_input = QLineEdit()
        self.recruiter_email_input = QLineEdit()
        self.recruiter_phone_input = QLineEdit()
        self.feedback_input = QTextEdit()
        self.feedback_input.setMaximumHeight(90)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(90)
        self.search_input = QLineEdit()
        self.filter_status_combo = QComboBox()
        self.filter_company_combo = QComboBox()
        self.filter_button = QPushButton("Filtrar")
        self.save_button = QPushButton("Salvar")
        self.delete_button = QPushButton("Excluir")
        self.curriculum_combo = QComboBox()
        self.select_curriculum_button = QPushButton("Selecionar currículo")
        self.analyze_resume_button = QPushButton("Analisar aderência")
        self.resume_match_label = QLabel("Currículo selecionado: nenhum | Aderência: não analisada")
        self.resume_match_details = QTextEdit()
        self.resume_match_details.setReadOnly(True)
        self.resume_match_details.setMaximumHeight(120)
        self.optimize_resume_button = QPushButton("Otimizar currículo")
        self.assisted_application_button = QPushButton("Abrir e preencher candidatura")
        self.assisted_application_button.setEnabled(False)
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
        self.select_curriculum_button.setEnabled(False)
        self.analyze_resume_button.setEnabled(False)
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
        self.job_combo.currentIndexChanged.connect(self._populate_salary_from_job)
        self._load_companies()
        self._load_curricula()
        self._load_applications()

    def refresh_reference_data(self) -> None:
        """Recarrega dados visíveis ao entrar ou retornar à página."""

        selected_application_id = self.current_application_id
        selected_company_id = self.company_combo.currentData()
        selected_curriculum_id = self.curriculum_combo.currentData()
        self._load_companies()
        if selected_company_id not in (None, ""):
            index = self.company_combo.findData(selected_company_id)
            if index >= 0:
                self.company_combo.setCurrentIndex(index)
        self._load_jobs()
        self._load_curricula()
        self._load_applications()
        if selected_curriculum_id not in (None, ""):
            index = self.curriculum_combo.findData(selected_curriculum_id)
            if index >= 0:
                self.curriculum_combo.setCurrentIndex(index)
        if selected_application_id is not None:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item is not None and int(item.text()) == selected_application_id:
                    self.table.selectRow(row)
                    break

    def _setup_controls(self) -> None:
        if self.application_follow_up_service is not None:
            self.next_action_combo.addItem("")
            self.next_action_combo.addItems(self.application_follow_up_service.ACTION_TYPES)
            self.follow_up_priority_combo.addItems(
                self.application_follow_up_service.PRIORITIES
            )
        for date_input in (
            self.application_date_input,
            self.next_follow_up_input,
            self.response_date_input,
            self.interview_date_input,
        ):
            date_input.setCalendarPopup(True)
            date_input.setDisplayFormat("dd/MM/yyyy")

        for optional_date_input in (
            self.next_follow_up_input,
            self.response_date_input,
            self.interview_date_input,
        ):
            optional_date_input.setMinimumDate(QDate(1900, 1, 1))
            optional_date_input.setSpecialValueText(" ")
            optional_date_input.setDate(optional_date_input.minimumDate())

        self.application_date_input.setDate(QDate.currentDate())

        self.interview_date_input.setReadOnly(True)
        self.interview_date_input.setCalendarPopup(False)
        self.interview_date_input.setToolTip(
            "Atualizado automaticamente ao agendar uma entrevista."
        )

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

        form_columns = QHBoxLayout()

        first_column = QFormLayout()
        first_column.addRow(QLabel("Empresa"), self.company_combo)
        first_column.addRow(QLabel("Vaga"), self.job_combo)
        first_column.addRow(QLabel("Status"), self.status_combo)
        first_column.addRow(QLabel("Data aplicação"), self.application_date_input)
        first_column.addRow(QLabel("Próximo follow-up"), self.next_follow_up_input)

        second_column = QFormLayout()
        second_column.addRow(QLabel("Data resposta"), self.response_date_input)
        second_column.addRow(QLabel("Data entrevista"), self.interview_date_input)
        second_column.addRow(QLabel("Currículo"), self.curriculum_combo)
        second_column.addRow(QLabel("Salário esperado"), self.salary_expected_input)
        second_column.addRow(QLabel("Salário oferecido"), self.salary_offered_input)

        third_column = QFormLayout()
        third_column.addRow(QLabel("Canal"), self.channel_input)
        third_column.addRow(QLabel("Recrutador"), self.recruiter_name_input)
        third_column.addRow(QLabel("E-mail"), self.recruiter_email_input)
        third_column.addRow(QLabel("Telefone"), self.recruiter_phone_input)

        form_columns.addLayout(first_column, 1)
        form_columns.addLayout(second_column, 1)
        form_columns.addLayout(third_column, 1)

        full_width_fields = QFormLayout()
        full_width_fields.addRow(QLabel("Feedback"), self.feedback_input)
        full_width_fields.addRow(QLabel("Observações"), self.notes_input)

        follow_up_layout = QGridLayout()
        follow_up_layout.addWidget(QLabel("Próxima ação"), 0, 0)
        follow_up_layout.addWidget(self.next_action_combo, 0, 1)
        follow_up_layout.addWidget(QLabel("Prioridade"), 0, 2)
        follow_up_layout.addWidget(self.follow_up_priority_combo, 0, 3)
        follow_up_layout.addWidget(QLabel("Horário"), 1, 0)
        follow_up_layout.addWidget(self.follow_up_time_input, 1, 1)
        follow_up_layout.addWidget(QLabel("Observação de acompanhamento"), 2, 0)
        follow_up_layout.addWidget(self.follow_up_note_input, 2, 1, 1, 3)
        follow_up_layout.addWidget(QLabel("Última interação"), 3, 0)
        follow_up_layout.addWidget(self.last_interaction_label, 3, 1, 1, 3)
        for column, button in enumerate(
            (
                self.register_interaction_button,
                self.complete_follow_up_button,
                self.postpone_follow_up_button,
                self.timeline_button,
            )
        ):
            follow_up_layout.addWidget(button, 4, column)
        self.register_interaction_button.clicked.connect(self._register_interaction)
        self.complete_follow_up_button.clicked.connect(self._complete_follow_up)
        self.postpone_follow_up_button.clicked.connect(self._postpone_follow_up)
        self.timeline_button.clicked.connect(self._show_timeline)
        follow_up_layout.addWidget(self.outlook_sync_button, 5, 0, 1, 4)
        self.outlook_sync_button.clicked.connect(self._sync_outlook_classic)

        actions = QGridLayout()
        action_buttons = (
            self.save_button,
            self.delete_button,
            self.select_curriculum_button,
            self.analyze_resume_button,
            self.optimize_resume_button,
            self.assisted_application_button,
            self.generate_structured_resume_button,
            self.export_effective_resume_docx_button,
            self.validate_structured_resume_quality_button,
        )
        for index, button in enumerate(action_buttons):
            actions.addWidget(button, index // 3, index % 3)
        self.save_button.clicked.connect(self._save_application)
        self.delete_button.clicked.connect(self._delete_application)
        self.select_curriculum_button.clicked.connect(self._select_curriculum)
        self.analyze_resume_button.clicked.connect(self._analyze_resume_match)
        self.optimize_resume_button.clicked.connect(self._optimize_resume)
        self.assisted_application_button.clicked.connect(self._prepare_assisted_application)
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

        self.content_layout.addLayout(search_layout)
        self.content_layout.addLayout(filter_layout)
        self.content_layout.addWidget(self.table)
        self.content_layout.addLayout(form_columns)
        self.content_layout.addLayout(full_width_fields)
        self.content_layout.addLayout(follow_up_layout)
        self.content_layout.addWidget(self.resume_match_label)
        self.content_layout.addWidget(self.resume_match_details)
        self.content_layout.addWidget(self.structured_resume_quality_label)
        self.content_layout.addWidget(self.structured_resume_quality_issues)
        self.content_layout.addWidget(self.candidate_decision_panel)
        self.content_layout.addWidget(self.resume_version_review_panel)
        self.content_layout.addWidget(self.effective_application_resume_preview_panel)
        self.content_layout.addWidget(self.optimization_status_label)
        self.content_layout.addLayout(actions)

    def _load_curricula(self) -> None:
        selected = self.curriculum_combo.currentData()
        self.curriculum_combo.clear()
        self.curriculum_combo.addItem("", "")
        for curriculum in self.curriculum_service.list_curricula():
            label = f"{curriculum.name} — {curriculum.version}"
            self.curriculum_combo.addItem(label, curriculum.id)
        if selected not in (None, ""):
            index = self.curriculum_combo.findData(selected)
            if index >= 0:
                self.curriculum_combo.setCurrentIndex(index)

    def _select_curriculum(self) -> None:
        if self.current_application_id is None:
            QMessageBox.information(self, "Currículo", "Selecione uma candidatura.")
            return
        curriculum_id = self.curriculum_combo.currentData()
        if curriculum_id in (None, ""):
            QMessageBox.warning(self, "Currículo", "Selecione um currículo cadastrado.")
            return
        associated = self.curriculum_service.associate_to_application(
            application_id=self.current_application_id,
            curriculum_id=int(curriculum_id),
        )
        if associated is None:
            QMessageBox.warning(self, "Currículo", "Não foi possível associar o currículo.")
            return
        self.resume_match_label.setText(
            f"Currículo selecionado: {self.curriculum_combo.currentText()} | Aderência: não analisada"
        )
        self.resume_match_details.clear()
        self.select_curriculum_button.setEnabled(True)
        self.analyze_resume_button.setEnabled(True)
        self.optimize_resume_button.setEnabled(False)

    def _analyze_resume_match(self) -> None:
        if self.current_application_id is None:
            QMessageBox.information(self, "Aderência", "Selecione uma candidatura.")
            return
        curriculum_id = self.curriculum_combo.currentData()
        if curriculum_id in (None, ""):
            QMessageBox.warning(self, "Aderência", "Selecione e associe um currículo.")
            return
        application = self.application_service.get_application(self.current_application_id)
        curricula = self.curriculum_service.list_curricula()
        curriculum = next(
            (item for item in curricula if int(item.id) == int(curriculum_id)),
            None,
        )
        if application is None or curriculum is None:
            QMessageBox.warning(self, "Aderência", "Dados da candidatura ou currículo indisponíveis.")
            return
        result = self.resume_match_service.analyze(application=application, curriculum=curriculum)
        if not result.has_vacancy_description:
            QMessageBox.warning(
                self,
                "Aderência",
                "A vaga vinculada não possui descrição no campo Observações da página Vagas.",
            )
            self.resume_match_label.setText(
                f"Currículo selecionado: {self.curriculum_combo.currentText()} | "
                "Aderência: descrição da vaga indisponível"
            )
            self.resume_match_details.clear()
            self.optimize_resume_button.setEnabled(False)
            return
        self._persist_resume_match_as_ats(
            application=application,
            curriculum=curriculum,
            result=result,
        )
        self._render_resume_match(result)

    def _persist_resume_match_as_ats(
        self,
        *,
        application: object,
        curriculum: object,
        result: ResumeMatchResult,
    ) -> None:
        """Make the saved adherence analysis available to the optimization workflow."""
        if self.ats_service is None:
            return
        application_id = getattr(application, "id", None)
        curriculum_id = getattr(curriculum, "id", None)
        if application_id is None or curriculum_id is None:
            return
        self.ats_service.persist_resume_match_result(
            application_id=int(application_id),
            curriculum_id=int(curriculum_id),
            result=result,
        )

    def _render_resume_match(self, result: ResumeMatchResult) -> None:
        self.resume_match_label.setText(
            f"Currículo selecionado: {self.curriculum_combo.currentText()} | "
            f"Aderência técnica atual: {result.score:.0f}%"
        )
        matched = ", ".join(result.matched_keywords[:12]) or "Nenhuma identificada"
        missing = ", ".join(result.missing_keywords[:12]) or "Nenhuma lacuna prioritária"
        html = f"""
        <table cellspacing="0" cellpadding="6" border="1" width="100%">
          <tr><th align="left">Critério</th><th>Atual</th><th>Adaptado</th></tr>
          <tr><td>Compatibilidade ATS</td><td align="center">{result.ats_score:.0f}%</td>
              <td align="center"><b>{result.adapted_ats_score:.0f}%</b></td></tr>
          <tr><td>Aderência técnica</td><td align="center">{result.score:.0f}%</td>
              <td align="center"><b>{result.adapted_score:.0f}%</b></td></tr>
          <tr><td>Probabilidade estimada de entrevista</td>
              <td align="center">{result.interview_probability_min:.0f}–{result.interview_probability_max:.0f}%</td>
              <td align="center"><b>{result.adapted_interview_probability_min:.0f}–{result.adapted_interview_probability_max:.0f}%</b></td></tr>
        </table>
        <p><b>Pontos aderentes:</b> {matched}</p>
        <p><b>Lacunas prioritárias:</b> {missing}</p>
        <p><i>O resultado adaptado é uma projeção após reorganizar e destacar informações verdadeiras.
        A probabilidade de entrevista é apenas um indicador comparativo e não representa garantia.</i></p>
        """
        self.resume_match_details.setHtml(html)
        self.optimize_resume_button.setEnabled(
            self._resume_optimization_view_model is not None
            and not self._resume_optimization_executor.is_running
        )

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

    def _populate_salary_from_job(self) -> None:
        job_id = self.job_combo.currentData()
        if job_id in (None, ""):
            self.salary_expected_input.clear()
            self.salary_offered_input.setText("A combinar")
            return
        job = self.job_service.get_job(int(job_id))
        if job is None:
            return
        offered = float(job.salary_min) if job.salary_min is not None else None
        ideal = float(job.salary_max) if job.salary_max is not None else None
        self.salary_expected_input.setText(
            f"{ideal:.2f}" if ideal is not None else ""
        )
        self.salary_offered_input.setText(
            f"{offered:.2f}" if offered is not None else "A combinar"
        )

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
            next_follow_up = self._optional_date_value(self.next_follow_up_input)
            response_date = self._optional_date_value(self.response_date_input)
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
                saved_application = self.application_service.create_application(
                    job_id=job_id_value,
                    company_id=company_id_value,
                    status=status,
                    application_date=application_date,
                    next_follow_up=next_follow_up,
                    response_date=response_date,
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
                saved_application = self.application_service.update_application(
                    self.current_application_id,
                    job_id=job_id_value,
                    company_id=company_id_value,
                    status=status,
                    application_date=application_date,
                    next_follow_up=next_follow_up,
                    response_date=response_date,
                    salary_expected=salary_expected,
                    salary_offered=salary_offered,
                    application_channel=channel,
                    recruiter_name=recruiter_name,
                    recruiter_email=recruiter_email,
                    recruiter_phone=recruiter_phone,
                    feedback=feedback,
                    notes=notes,
                )

            if saved_application is not None:
                saved_application_id = int(saved_application.id)
                self.current_application_id = saved_application_id
                self._save_follow_up_state(saved_application_id)
                self._load_applications()
                self._select_application_row(saved_application_id)
            else:
                self._load_applications()
        except ValueError as exc:
            QMessageBox.warning(self, "Dados inválidos", str(exc))
        except Exception as exc:  # pragma: no cover - defensive UI handling
            QMessageBox.critical(self, "Erro", str(exc))

    def _require_follow_up(self) -> tuple[int, _FollowUpData]:
        if self.current_application_id is None:
            raise ValueError("Selecione uma candidatura.")
        if self.application_follow_up_service is None:
            raise ValueError("Acompanhamento não configurado.")
        return self.current_application_id, self.application_follow_up_service

    def _sync_outlook_classic(self) -> None:
        if self.current_application_id is None:
            QMessageBox.information(
                self, "Outlook Classic", "Selecione uma candidatura para sincronizar."
            )
            return
        if self.communications_service is None:
            QMessageBox.warning(
                self, "Outlook Classic", "Integração com Outlook Classic não configurada."
            )
            return
        if self._communications_executor.is_running:
            return

        application_id = self.current_application_id
        dialog = QProgressDialog("Preparando Outlook Classic...", "", 0, 100, self)
        dialog.setWindowTitle("Sincronizando Outlook Classic")
        dialog.setCancelButton(None)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.setValue(0)
        self._outlook_sync_progress = dialog
        self.outlook_sync_button.setEnabled(False)
        dialog.show()

        self._communications_executor.execute_with_context(
            lambda emit, _token: self.communications_service.sync_application(
                application_id,
                progress=emit,
            )
        )

    def _on_outlook_sync_progress(self, payload: object) -> None:
        dialog = self._outlook_sync_progress
        if dialog is None:
            return
        if isinstance(payload, tuple) and len(payload) == 2:
            value, message = payload
            dialog.setValue(int(value))
            dialog.setLabelText(str(message))

    def _on_outlook_sync_succeeded(self, result: object) -> None:
        if self.current_application_id is not None:
            self._load_follow_up_state(self.current_application_id)

        imported = int(getattr(result, "imported_messages", 0))
        skipped = int(getattr(result, "skipped_duplicates", 0))
        matched = int(getattr(result, "matched_messages", 0))

        QMessageBox.information(
            self,
            "Outlook Classic",
            f"Sincronização concluída. Encontradas: {matched} | "
            f"Importadas: {imported} | Já registradas: {skipped}.",
        )

    def _on_outlook_sync_failed(self, error: object) -> None:
        QMessageBox.warning(self, "Outlook Classic", str(error))

    def _on_outlook_sync_finished(self) -> None:
        dialog = self._outlook_sync_progress
        if dialog is not None:
            dialog.close()
        self._outlook_sync_progress = None
        self.outlook_sync_button.setEnabled(
            self.current_application_id is not None and self.communications_service is not None
        )

    def _register_interaction(self) -> None:
        try:
            application_id, service = self._require_follow_up()
            interaction_type, accepted = QInputDialog.getItem(
                self,
                "Registrar interação",
                "Tipo",
                service.INTERACTION_TYPES,
                editable=False,
            )
            if not accepted:
                return
            summary, accepted = QInputDialog.getText(
                self, "Registrar interação", "Resumo do evento real"
            )
            if not accepted:
                return
            service.register_interaction(
                application_id,
                interaction_type=interaction_type,
                summary=summary,
            )
            self._load_follow_up_state(application_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Acompanhamento", str(exc))


    def _complete_follow_up(self) -> None:
        try:
            application_id, service = self._require_follow_up()
            service.complete_follow_up(application_id)
            self._load_follow_up_state(application_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Acompanhamento", str(exc))

    def _postpone_follow_up(self) -> None:
        try:
            application_id, service = self._require_follow_up()
            selected = self.next_follow_up_input.date().toPython()
            service.postpone_follow_up(application_id, selected)
            self._load_follow_up_state(application_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Acompanhamento", str(exc))

    def _show_timeline(self) -> None:
        try:
            application_id, service = self._require_follow_up()
            timeline = service.get_timeline(application_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Acompanhamento", str(exc))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Timeline da candidatura")
        dialog.resize(920, 520)
        layout = QVBoxLayout(dialog)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Tipo"))
        type_filter = QComboBox()
        type_filter.addItem("Todos")
        event_types = sorted(
            {str(item.interaction_type) for item in timeline},
            key=str.casefold,
        )
        type_filter.addItems(event_types)
        filter_row.addWidget(type_filter)
        counter = QLabel()
        filter_row.addStretch(1)
        filter_row.addWidget(counter)
        layout.addLayout(filter_row)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(
            ["Data/Hora", "Tipo", "Resumo", "Origem", "Referência", "ID"]
        )
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(table)

        def render(selected_type: str = "Todos") -> None:
            filtered = [
                item
                for item in timeline
                if selected_type == "Todos"
                or str(item.interaction_type) == selected_type
            ]
            table.setRowCount(len(filtered))
            for row, item in enumerate(filtered):
                reference = str(item.reference_type or "")
                reference_id = "" if item.reference_id is None else str(item.reference_id)
                values = (
                    f"{item.occurred_at:%d/%m/%Y %H:%M}",
                    str(item.interaction_type),
                    str(item.summary),
                    str(item.origin),
                    reference,
                    reference_id,
                )
                for column, value in enumerate(values):
                    table.setItem(row, column, QTableWidgetItem(value))
            counter.setText(f"{len(filtered)} evento(s)")

        type_filter.currentTextChanged.connect(render)
        render()
        dialog.exec()

    def _load_follow_up_state(self, application_id: int) -> None:
        if self.application_follow_up_service is None:
            return
        state = self.application_follow_up_service.get_state(application_id)
        action_index = self.next_action_combo.findText(state.next_action)
        if action_index >= 0:
            self.next_action_combo.setCurrentIndex(action_index)
        priority_index = self.follow_up_priority_combo.findText(state.priority)
        if priority_index >= 0:
            self.follow_up_priority_combo.setCurrentIndex(priority_index)
        self.follow_up_note_input.setText(state.note)
        self.follow_up_time_input.setText(state.follow_up_time)
        if state.last_interaction_at is None:
            self.last_interaction_label.setText("Nenhuma interação registrada")
        else:
            self.last_interaction_label.setText(
                f"{state.last_interaction_type} · "
                f"{state.last_interaction_at:%d/%m/%Y %H:%M}"
            )

    def _save_follow_up_state(self, application_id: int) -> None:
        if self.application_follow_up_service is None:
            return
        if not self.next_action_combo.currentText():
            return
        self.application_follow_up_service.set_next_action(
            application_id,
            action=self.next_action_combo.currentText(),
            follow_up_date=self.next_follow_up_input.date().toPython()
            if self.next_follow_up_input.text().strip()
            else None,
            priority=self.follow_up_priority_combo.currentText(),
            follow_up_time=self.follow_up_time_input.text().strip(),
            note=self.follow_up_note_input.text(),
        )

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

    def _prepare_assisted_application(self) -> None:
        if self.current_application_id is None or self.assisted_application_service is None:
            QMessageBox.information(self, "Candidatura assistida", "Selecione uma candidatura.")
            return
        application = self.application_service.get_application(self.current_application_id)
        if application is None:
            QMessageBox.warning(self, "Candidatura assistida", "Candidatura não encontrada.")
            return
        job = self.job_service.get_job(int(application.job_id))
        application_url = (
            ""
            if job is None
            else str(getattr(job, "application_url", "") or "").strip()
        )
        job_url = (
            ""
            if job is None
            else str(getattr(job, "job_url", "") or "").strip()
        )
        target_url = application_url or job_url
        if not target_url:
            QMessageBox.warning(
                self,
                "Candidatura assistida",
                "Cadastre a URL da candidatura ou a URL da vaga antes de continuar.",
            )
            return
        profile = self.assisted_application_service.profile_store.load()
        dialog = ApplicantProfileDialog(profile, self)
        if dialog.exec() != QDialog.Accepted:
            return
        profile = dialog.profile()
        if not profile.full_name or not profile.email:
            QMessageBox.warning(self, "Candidatura assistida", "Informe nome completo e e-mail.")
            return
        curriculum_id = self.curriculum_combo.currentData()
        resume_path = None
        if curriculum_id not in (None, ""):
            resolver = getattr(self.curriculum_service, "resolve_document_path", None)
            if callable(resolver):
                resume_path = resolver(int(curriculum_id))
        self._assisted_application_progress = QProgressDialog(
            "Preparando candidatura...", "Cancelar", 0, 100, self
        )
        self._assisted_application_progress.setWindowTitle("Candidatura assistida")
        self._assisted_application_progress.setWindowModality(Qt.NonModal)
        self._assisted_application_progress.setAutoClose(False)
        self._assisted_application_progress.setValue(0)
        self._assisted_application_progress.show()
        self.assisted_application_button.setEnabled(False)
        service = self.assisted_application_service
        self._assisted_application_executor.execute_with_context(
            lambda emit, _token: service.prepare(
                job_url=target_url,
                source_url=job_url if application_url and job_url != target_url else None,
                profile=profile,
                resume_path=resume_path,
                progress=emit,
            )
        )

    def _on_assisted_application_progress(self, payload: object) -> None:
        if self._assisted_application_progress is None:
            return
        if isinstance(payload, tuple) and len(payload) == 2:
            value, message = payload
            self._assisted_application_progress.setValue(int(value))
            self._assisted_application_progress.setLabelText(str(message))

    def _on_assisted_application_succeeded(self, result: object) -> None:
        if self._assisted_application_progress is not None:
            self._assisted_application_progress.close()
            self._assisted_application_progress = None
        self.assisted_application_button.setEnabled(True)
        if not isinstance(result, AssistedApplicationResult):
            return
        message = (
            f"Plataforma: {result.platform}\n"
            f"Campos preenchidos: {result.fields_filled}\n"
            f"Currículo anexado: {'sim' if result.resume_attached else 'não'}\n\n"
            "A candidatura foi enviada no navegador?"
        )
        if result.linkedin_restricted_mode:
            message = (
                "O LinkedIn foi aberto em modo manual para proteger sua conta.\n\n" + message
            )
        answer = QMessageBox.question(
            self, "Candidatura assistida", message,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.status_combo.setCurrentText("Aplicada")
            self.application_date_input.setDate(QDate.currentDate())
            self._save_application()

    def _on_assisted_application_failed(self, error: object) -> None:
        if self._assisted_application_progress is not None:
            self._assisted_application_progress.close()
            self._assisted_application_progress = None
        self.assisted_application_button.setEnabled(True)
        QMessageBox.critical(self, "Candidatura assistida", str(error))

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
            self.select_curriculum_button.setEnabled(False)
            self.analyze_resume_button.setEnabled(False)
            self.optimize_resume_button.setEnabled(False)
            self.assisted_application_button.setEnabled(False)
            self.outlook_sync_button.setEnabled(False)
            self.generate_structured_resume_button.setEnabled(False)
            self.candidate_decision_panel.show_empty_state()
            self.candidate_decision_panel.render_actions(())
            self.resume_version_review_panel.show_empty_state()
            self.effective_application_resume_preview_panel.show_empty_state()
            return
        row = selected_rows[0].row()
        self.current_application_id = int(self.table.item(row, 0).text())
        self.select_curriculum_button.setEnabled(True)
        self.assisted_application_button.setEnabled(self.assisted_application_service is not None)
        self.outlook_sync_button.setEnabled(self.communications_service is not None)
        self.analyze_resume_button.setEnabled(False)
        self.optimize_resume_button.setEnabled(False)
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
            self._load_follow_up_state(self.current_application_id)
            company_index = self.company_combo.findData(application.company_id)
            if company_index >= 0:
                self.company_combo.setCurrentIndex(company_index)
            self._load_jobs()
            job_index = self.job_combo.findData(application.job_id)
            if job_index >= 0:
                self.job_combo.setCurrentIndex(job_index)
            self.status_combo.setCurrentText(application.status or "")
            application_date = application.application_date
            if application_date is None:
                self.application_date_input.setDate(QDate.currentDate())
            else:
                self.application_date_input.setDate(
                    QDate(application_date.year, application_date.month, application_date.day)
                )

            for widget, value in (
                (self.next_follow_up_input, application.next_follow_up),
                (self.response_date_input, application.response_date),
                (self.interview_date_input, application.interview_date),
            ):
                if value is None:
                    widget.setDate(widget.minimumDate())
                else:
                    widget.setDate(QDate(value.year, value.month, value.day))
            self.salary_expected_input.setText(
                "" if application.salary_expected is None else str(application.salary_expected)
            )
            self.salary_offered_input.setText(
                "A combinar"
                if application.salary_offered is None
                else str(application.salary_offered)
            )
            self.channel_input.setText(application.application_channel or "")
            self.recruiter_name_input.setText(application.recruiter_name or "")
            self.recruiter_email_input.setText(application.recruiter_email or "")
            self.recruiter_phone_input.setText(application.recruiter_phone or "")
            self.feedback_input.setPlainText(application.feedback or "")
            self.notes_input.setPlainText(application.notes or "")
            curriculum_id = getattr(application, "curriculum_id", None)
            curriculum_index = self.curriculum_combo.findData(curriculum_id)
            self.curriculum_combo.setCurrentIndex(curriculum_index if curriculum_index >= 0 else 0)
            if curriculum_index >= 0:
                self.resume_match_label.setText(
                    f"Currículo selecionado: {self.curriculum_combo.currentText()} | "
                    "Aderência: não analisada"
                )
                self.analyze_resume_button.setEnabled(True)
                self.optimize_resume_button.setEnabled(
                    self._resume_optimization_view_model is not None
                    and not self._resume_optimization_executor.is_running
                )
                curriculum = next(
                    (
                        item
                        for item in self.curriculum_service.list_curricula()
                        if int(item.id) == int(curriculum_id)
                    ),
                    None,
                )
                cached = (
                    None
                    if curriculum is None
                    else self.resume_match_service.get_cached(
                        application=application,
                        curriculum=curriculum,
                    )
                )
                if cached is not None:
                    self._persist_resume_match_as_ats(
                        application=application,
                        curriculum=curriculum,
                        result=cached,
                    )
                    self._render_resume_match(cached)
            else:
                self.resume_match_label.setText(
                    "Currículo selecionado: nenhum | Aderência: não analisada"
                )
                self.resume_match_details.clear()

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
        selected_curriculum_id = self.curriculum_combo.currentData()
        if selected_curriculum_id in (None, ""):
            QMessageBox.information(
                self,
                "Otimizar currículo",
                "Selecione e associe um currículo antes de iniciar a otimização.",
            )
            return

        source_curriculum_id = int(selected_curriculum_id)
        self._optimization_source_curriculum_id = source_curriculum_id
        self._active_long_running_task = "optimization"
        self._show_optimization_progress()

        def optimize_task(emit_progress, cancellation_token):
            emit_progress((5, "Preparando dados da candidatura e do currículo..."))
            state = self._resume_optimization_view_model.optimize(application_id)
            emit_progress((70, "Conteúdo otimizado. Cadastrando a nova versão..."))
            if not state.success:
                return state, None
            if cancellation_token.is_cancellation_requested:
                raise RuntimeError("Otimização cancelada.")

            creator = getattr(self.curriculum_service, "create_optimized_curriculum", None)
            if creator is None:
                raise RuntimeError("O serviço de currículos não permite criar a versão otimizada.")

            optimized = creator(
                source_curriculum_id=source_curriculum_id,
                generated_version=state.version,
            )
            if optimized is None or getattr(optimized, "id", None) is None:
                raise RuntimeError("A nova versão do currículo não pôde ser cadastrada.")

            emit_progress((90, "Associando o novo currículo à candidatura..."))
            associated = self.curriculum_service.associate_to_application(
                application_id=application_id,
                curriculum_id=int(optimized.id),
            )
            if associated is None:
                raise RuntimeError("A nova versão foi criada, mas não pôde ser associada à candidatura.")
            emit_progress((100, "Nova versão criada com sucesso."))
            return state, optimized

        try:
            self._resume_optimization_executor.execute_with_context(optimize_task)
        except Exception as error:
            self._on_optimization_failed(error)
            self._on_long_running_task_finished()

    def _show_optimization_progress(self) -> None:
        dialog = QProgressDialog(
            "Preparando otimização...",
            "",
            0,
            100,
            self,
        )
        dialog.setWindowTitle("Otimizar currículo")
        dialog.setCancelButton(None)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.setMinimumDuration(0)
        dialog.setValue(0)
        dialog.show()
        self._optimization_progress_dialog = dialog

    def _on_optimization_progress(self, progress: object) -> None:
        if self._active_long_running_task != "optimization":
            return
        dialog = self._optimization_progress_dialog
        if dialog is None:
            return
        value = 0
        message = ""
        if isinstance(progress, tuple) and len(progress) == 2:
            value, message = progress
        elif isinstance(progress, dict):
            value = progress.get("value", 0)
            message = progress.get("message", "")
        elif isinstance(progress, int):
            value = progress
        dialog.setValue(max(0, min(100, int(value))))
        if message:
            dialog.setLabelText(str(message))

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
        self.select_curriculum_button.setEnabled(False)
        self.analyze_resume_button.setEnabled(False)
        self.generate_structured_resume_button.setEnabled(False)
        self.optimization_status_label.setText("Otimizando currículo...")

    def _on_optimization_succeeded(self, result: object) -> None:
        optimized = None
        state = result
        if isinstance(result, tuple) and len(result) == 2:
            state, optimized = result
        if not isinstance(state, ResumeOptimizationViewState):
            self._on_optimization_failed(
                RuntimeError("A otimização retornou um resultado inesperado.")
            )
            return
        if state.application_id != self.current_application_id:
            return

        message = (
            state.message
            if state.version is None
            else f"{state.message} Versão gerada: {state.version}."
        )
        if not state.success:
            self.optimization_status_label.setText(f"{state.title}: {message}")
            QMessageBox.warning(self, state.title, message)
            return

        if optimized is None:
            source_curriculum_id = self._optimization_source_curriculum_id
            creator = getattr(self.curriculum_service, "create_optimized_curriculum", None)
            if source_curriculum_id in (None, "") or creator is None:
                self._on_optimization_failed(
                    RuntimeError("Não foi possível identificar o currículo de origem.")
                )
                return
            optimized = creator(
                source_curriculum_id=int(source_curriculum_id),
                generated_version=state.version,
            )
            if optimized is None:
                self._on_optimization_failed(
                    RuntimeError("Não foi possível cadastrar a nova versão em Currículos.")
                )
                return
            associated = self.curriculum_service.associate_to_application(
                application_id=state.application_id,
                curriculum_id=int(optimized.id),
            )
            if associated is None:
                self._on_optimization_failed(
                    RuntimeError("O currículo foi criado, mas não pôde ser associado à candidatura.")
                )
                return

        self._load_curricula()
        optimized_index = self.curriculum_combo.findData(optimized.id)
        if optimized_index >= 0:
            self.curriculum_combo.setCurrentIndex(optimized_index)
        self.resume_match_label.setText(
            f"Currículo selecionado: {self.curriculum_combo.currentText()} | "
            "Aderência: nova versão otimizada"
        )
        self.optimization_status_label.setText(
            f"{state.title}: currículo cadastrado como "
            f"{optimized.name} — {optimized.version}."
        )
        self.refresh_reference_data()
        callback = self._on_optimized_curriculum_created_callback
        if callback is not None:
            callback(int(optimized.id))

    def _on_optimization_failed(self, error: Exception) -> None:
        message = f"Não foi possível otimizar o currículo: {error}"
        self.optimization_status_label.setText(message)
        QMessageBox.critical(self, "Otimização de currículo", message)

    def _on_optimization_finished(self) -> None:
        if self._optimization_progress_dialog is not None:
            self._optimization_progress_dialog.close()
            self._optimization_progress_dialog.deleteLater()
            self._optimization_progress_dialog = None
        self._optimization_source_curriculum_id = None
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

    def _select_application_row(self, application_id: int) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None and int(item.text()) == application_id:
                self.table.selectRow(row)
                return

    def _clear_form(self) -> None:
        self.current_application_id = None
        self.outlook_sync_button.setEnabled(False)
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
        self.application_date_input.setDate(QDate.currentDate())
        self.next_follow_up_input.setDate(self.next_follow_up_input.minimumDate())
        self.response_date_input.setDate(self.response_date_input.minimumDate())
        self.interview_date_input.setDate(self.interview_date_input.minimumDate())
        self.curriculum_combo.setCurrentIndex(0)
        self.resume_match_label.setText("Currículo selecionado: nenhum | Aderência: não analisada")
        self.resume_match_details.clear()
        self.salary_expected_input.clear()
        self.salary_offered_input.clear()
        self.channel_input.clear()
        self.recruiter_name_input.clear()
        self.recruiter_email_input.clear()
        self.recruiter_phone_input.clear()
        self.feedback_input.clear()
        self.notes_input.clear()

    @staticmethod
    def _optional_date_value(date_input: QDateEdit) -> str | None:
        value = date_input.date()
        if value == date_input.minimumDate():
            return None
        return value.toString("yyyy-MM-dd")

    def _parse_optional_number(self, value: str) -> float | None:
        normalized = value.strip()
        if not normalized or normalized.casefold() in {"a combinar", "combinar"}:
            return None
        return float(normalized.replace(",", "."))
