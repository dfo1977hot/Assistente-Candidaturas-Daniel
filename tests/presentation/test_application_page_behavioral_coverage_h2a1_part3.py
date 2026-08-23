from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from PySide6.QtWidgets import QDialog, QMessageBox, QTableWidgetItem

from acd.presentation.models.resume_optimization_view_state import (
    ResumeOptimizationViewState,
)
import acd.presentation.pages.application_page as application_page_module
from acd.presentation.pages.application_page import ApplicationPage


class _ApplicationService:
    def __init__(self) -> None:
        company = SimpleNamespace(
            id=1,
            name="Empresa Alpha",
        )
        job = SimpleNamespace(
            id=10,
            title="Engenheiro de Produção",
        )

        self.application = SimpleNamespace(
            id=300,
            company=company,
            company_id=1,
            job=job,
            job_id=10,
            curriculum_id=100,
            status="Aplicada",
            application_date=datetime(2026, 8, 10),
            next_follow_up=datetime(2026, 8, 20),
            response_date=None,
            interview_date=None,
            salary_expected=12000.0,
            salary_offered=None,
            application_channel="LinkedIn",
            recruiter_name="Maria",
            recruiter_email="maria@example.com",
            recruiter_phone="11999999999",
            feedback="",
            notes="",
        )

    def list_applications(self):
        return [self.application]

    def search_applications(self, query: str):
        del query
        return [self.application]

    def filter_applications(self, **filters):
        del filters
        return [self.application]

    def get_application(self, application_id: int):
        if application_id == 300:
            return self.application
        return None


class _CompanyService:
    def list_companies(self):
        return [
            SimpleNamespace(
                id=1,
                name="Empresa Alpha",
            ),
            SimpleNamespace(
                id=2,
                name="Empresa Beta",
            ),
        ]


class _JobService:
    def __init__(self) -> None:
        self.job = SimpleNamespace(
            id=10,
            title="Engenheiro de Produção",
            company_id=1,
            salary_min=9000,
            salary_max=12000,
            application_url="https://example.com/apply",
            job_url="https://example.com/job",
        )

    def filter_jobs(self, **filters):
        company_id = filters.get("company_id")
        if company_id == 1:
            return [self.job]
        return []

    def get_job(self, job_id: int):
        if job_id == 10:
            return self.job
        return None


class _CurriculumService:
    def __init__(self) -> None:
        self.original = SimpleNamespace(
            id=100,
            name="Currículo Origem",
            version="1",
        )
        self.optimized = SimpleNamespace(
            id=200,
            name="Currículo Otimizado",
            version="2",
        )

        self.created: list[tuple[int, str | None]] = []
        self.associated: list[tuple[int, int]] = []
        self.create_result = self.optimized
        self.association_result = SimpleNamespace(id=1)

    def list_curricula(self):
        return [
            self.original,
            self.optimized,
        ]

    def resolve_document_path(self, curriculum_id: int):
        if curriculum_id == 100:
            return "C:/temp/curriculo.docx"
        return None

    def create_optimized_curriculum(
        self,
        *,
        source_curriculum_id: int,
        generated_version: str | None = None,
    ):
        self.created.append(
            (
                source_curriculum_id,
                generated_version,
            )
        )
        return self.create_result

    def associate_to_application(
        self,
        *,
        application_id: int,
        curriculum_id: int,
    ):
        self.associated.append(
            (
                application_id,
                curriculum_id,
            )
        )
        return self.association_result


class _ResumeMatchService:
    def __init__(self) -> None:
        self.cached = SimpleNamespace(
            has_vacancy_description=True,
            score=82.0,
            overall_score=82.0,
            classification="Alta",
            ats_score=70.0,
            adapted_ats_score=88.0,
            adapted_score=91.0,
            interview_probability_min=30.0,
            interview_probability_max=45.0,
            adapted_interview_probability_min=55.0,
            adapted_interview_probability_max=70.0,
            requirements=(
                SimpleNamespace(
                    category="Metodologias / Qualidade",
                    requirement="Experiência com Lean",
                    evidence="Experiência comprovada com Lean",
                    score=100.0,
                    status="Forte",
                ),
                SimpleNamespace(
                    category="Experiência",
                    requirement="Experiência com PCP",
                    evidence="Experiência comprovada com PCP",
                    score=100.0,
                    status="Forte",
                ),
                SimpleNamespace(
                    category="Sistemas e ferramentas",
                    requirement="Conhecimento em SAP",
                    evidence="Não evidenciado no currículo.",
                    score=0.0,
                    status="Gap",
                ),
            ),
            dimension_scores=(
                SimpleNamespace(
                    name="Metodologias / Qualidade",
                    score=100.0,
                ),
                SimpleNamespace(
                    name="Sistemas e ferramentas",
                    score=0.0,
                ),
            ),
            strengths=(
                "Experiência com Lean",
                "Experiência com PCP",
            ),
            gaps=(
                "Conhecimento em SAP",
            ),
            differentials=(
                "Experiência em melhoria contínua",
            ),
            recommendation=(
                "Aderência alta. Recomenda-se a candidatura com adaptação "
                "direcionada do currículo."
            ),
            adaptation_strategy=(
                "Priorizar experiências aderentes aos requisitos da vaga.",
                "Reforçar palavras-chave verdadeiras sem criar competências.",
            ),
            matched_keywords=(
                "Lean",
                "PCP",
            ),
            missing_keywords=(
                "SAP",
            ),
        )
        self.cached_calls: list[tuple[object, object]] = []

    def analyze(self, *, application, curriculum):
        del application, curriculum
        return self.cached

    def get_cached(
        self,
        *,
        application,
        curriculum,
    ):
        self.cached_calls.append(
            (
                application,
                curriculum,
            )
        )
        return self.cached


class _AtsService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def persist_resume_match_result(self, **kwargs):
        self.calls.append(dict(kwargs))


class _ProfileStore:
    def load(self):
        return SimpleNamespace(
            full_name="Daniel Oliveira",
            email="daniel@example.com",
        )


class _AssistedApplicationService:
    def __init__(self) -> None:
        self.profile_store = _ProfileStore()
        self.calls: list[dict[str, object]] = []

    def prepare(
        self,
        *,
        job_url,
        source_url,
        profile,
        resume_path,
        progress,
    ):
        self.calls.append(
            {
                "job_url": job_url,
                "source_url": source_url,
                "profile": profile,
                "resume_path": resume_path,
            }
        )

        progress(
            (
                50,
                "Preparando candidatura",
            )
        )

        return SimpleNamespace()


class _Executor:
    def __init__(self) -> None:
        self.is_running = False
        self.tasks = []

    def execute_with_context(self, task):
        self.tasks.append(task)

        result = task(
            lambda _payload: None,
            None,
        )

        return result


class _OptimizationViewModel:
    def optimize(self, application_id: int):
        del application_id
        return None


def _page(
    *,
    assisted_application_service=None,
    optimization_view_model=None,
):
    applications = _ApplicationService()
    jobs = _JobService()
    curricula = _CurriculumService()
    resume_match = _ResumeMatchService()
    ats = _AtsService()

    page = ApplicationPage(
        application_service=applications,  # type: ignore[arg-type]
        company_service=_CompanyService(),  # type: ignore[arg-type]
        job_service=jobs,  # type: ignore[arg-type]
        curriculum_service=curricula,  # type: ignore[arg-type]
        resume_match_service=resume_match,  # type: ignore[arg-type]
        ats_service=ats,  # type: ignore[arg-type]
        assisted_application_service=assisted_application_service,  # type: ignore[arg-type]
        resume_optimization_view_model=optimization_view_model,  # type: ignore[arg-type]
    )

    return (
        page,
        applications,
        jobs,
        curricula,
        resume_match,
        ats,
    )


def test_refresh_reference_data_restores_all_selected_items(
    qapp,
) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
    ) = _page()

    page.company_combo.setCurrentIndex(
        page.company_combo.findData(1)
    )
    qapp.processEvents()

    page.curriculum_combo.setCurrentIndex(
        page.curriculum_combo.findData(100)
    )

    page.current_application_id = 300
    page.table.selectRow(0)

    page.refresh_reference_data()
    qapp.processEvents()

    assert page.company_combo.currentData() == 1
    assert page.curriculum_combo.currentData() == 100
    assert page.current_application_id == 300

    selected_rows = page.table.selectionModel().selectedRows()

    assert len(selected_rows) == 1
    assert selected_rows[0].row() == 0
    assert page.table.item(0, 0).text() == "300"


def test_refresh_reference_data_handles_missing_previous_values(
    qapp,
) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
    ) = _page()

    page.current_application_id = None
    page.company_combo.setCurrentIndex(0)
    page.curriculum_combo.setCurrentIndex(0)

    page.refresh_reference_data()
    qapp.processEvents()

    assert page.company_combo.currentIndex() == 0
    assert page.curriculum_combo.currentIndex() == 0
    assert page.table.rowCount() == 1


def test_assisted_application_runs_full_dialog_and_executor_path(
    qapp,
    monkeypatch,
) -> None:
    assisted = _AssistedApplicationService()

    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
    ) = _page(
        assisted_application_service=assisted,
    )

    page.current_application_id = 300
    page.company_combo.setCurrentIndex(
        page.company_combo.findData(1)
    )
    qapp.processEvents()

    page.job_combo.setCurrentIndex(
        page.job_combo.findData(10)
    )

    page.curriculum_combo.setCurrentIndex(
        page.curriculum_combo.findData(100)
    )

    profile = SimpleNamespace(
        full_name="Daniel Oliveira",
        email="daniel@example.com",
    )

    class _FakeApplicantProfileDialog:
        def __init__(self, current_profile, parent) -> None:
            self.current_profile = current_profile
            self.parent = parent

        def exec(self):
            return QDialog.Accepted

        def profile(self):
            return profile

    monkeypatch.setattr(
        application_page_module,
        "ApplicantProfileDialog",
        _FakeApplicantProfileDialog,
    )

    executor = _Executor()
    page._assisted_application_executor = executor  # type: ignore[assignment]

    page._prepare_assisted_application()

    assert len(executor.tasks) == 1
    assert len(assisted.calls) == 1

    call = assisted.calls[0]

    assert call["job_url"] == "https://example.com/apply"
    assert call["source_url"] == "https://example.com/job"
    assert call["profile"] is profile
    assert call["resume_path"] == "C:/temp/curriculo.docx"

    assert page._assisted_application_progress is not None
    assert not page.assisted_application_button.isEnabled()

    page._assisted_application_progress.close()


def test_assisted_application_stops_when_profile_dialog_is_cancelled(
    qapp,
    monkeypatch,
) -> None:
    assisted = _AssistedApplicationService()

    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
    ) = _page(
        assisted_application_service=assisted,
    )

    page.current_application_id = 300

    class _CancelledApplicantProfileDialog:
        def __init__(self, current_profile, parent) -> None:
            del current_profile, parent

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(
        application_page_module,
        "ApplicantProfileDialog",
        _CancelledApplicantProfileDialog,
    )

    page._prepare_assisted_application()

    assert assisted.calls == []
    assert page._assisted_application_progress is None


def test_assisted_application_rejects_profile_without_required_fields(
    qapp,
    monkeypatch,
) -> None:
    assisted = _AssistedApplicationService()

    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
    ) = _page(
        assisted_application_service=assisted,
    )

    page.current_application_id = 300

    class _InvalidApplicantProfileDialog:
        def __init__(self, current_profile, parent) -> None:
            del current_profile, parent

        def exec(self):
            return QDialog.Accepted

        def profile(self):
            return SimpleNamespace(
                full_name="",
                email="",
            )

    monkeypatch.setattr(
        application_page_module,
        "ApplicantProfileDialog",
        _InvalidApplicantProfileDialog,
    )

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._prepare_assisted_application()

    assert warnings == [
        "Informe nome completo e e-mail."
    ]
    assert assisted.calls == []


def test_row_selection_loads_cached_resume_match(
    qapp,
) -> None:
    (
        page,
        applications,
        _jobs,
        _curricula,
        resume_match,
        ats,
    ) = _page(
        optimization_view_model=_OptimizationViewModel(),
    )

    assert page.table.rowCount() == 1

    page.table.selectRow(0)
    qapp.processEvents()

    assert page.current_application_id == 300
    assert page.curriculum_combo.currentData() == 100

    assert resume_match.cached_calls == [
        (
            applications.application,
            page.curriculum_service.original,
        )
    ]

    assert ats.calls
    assert ats.calls[-1]["application_id"] == 300
    assert ats.calls[-1]["curriculum_id"] == 100

    assert "82%" in page.resume_match_label.text()
    assert "Lean" in page.resume_match_details.toPlainText()
    assert page.analyze_resume_button.isEnabled()
    assert page.optimize_resume_button.isEnabled()


def test_row_selection_without_matching_curriculum_clears_match(
    qapp,
) -> None:
    (
        page,
        applications,
        _jobs,
        _curricula,
        resume_match,
        ats,
    ) = _page()

    applications.application.curriculum_id = 999

    page.table.selectRow(0)
    qapp.processEvents()

    assert page.current_application_id == 300
    assert page.curriculum_combo.currentIndex() == 0
    assert resume_match.cached_calls == []
    assert ats.calls == []
    assert "nenhum" in page.resume_match_label.text().casefold()
    assert page.resume_match_details.toPlainText() == ""


def test_optimization_creates_and_associates_new_curriculum(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        curricula,
        _resume_match,
        _ats,
    ) = _page(
        optimization_view_model=_OptimizationViewModel(),
    )

    page.current_application_id = 300
    page._optimization_source_curriculum_id = 100

    callback_ids: list[int] = []
    page._on_optimized_curriculum_created_callback = callback_ids.append

    refresh_calls: list[bool] = []

    monkeypatch.setattr(
        page,
        "refresh_reference_data",
        lambda: refresh_calls.append(True),
    )

    state = ResumeOptimizationViewState(
        application_id=300,
        status="completed",
        title="Otimização concluída",
        message="Currículo otimizado",
        success=True,
        version="2",
    )

    page._on_optimization_succeeded(state)

    assert curricula.created == [
        (
            100,
            "2",
        )
    ]

    assert curricula.associated == [
        (
            300,
            200,
        )
    ]

    assert page.curriculum_combo.currentData() == 200
    assert "nova versão otimizada" in page.resume_match_label.text()
    assert "Currículo Otimizado" in page.optimization_status_label.text()
    assert refresh_calls == [True]
    assert callback_ids == [200]


def test_optimization_without_source_curriculum_fails_cleanly(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        curricula,
        _resume_match,
        _ats,
    ) = _page()

    page.current_application_id = 300
    page._optimization_source_curriculum_id = None

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    state = ResumeOptimizationViewState(
        application_id=300,
        status="completed",
        title="Otimização",
        message="Concluída",
        success=True,
        version="2",
    )

    page._on_optimization_succeeded(state)

    assert curricula.created == []
    assert curricula.associated == []
    assert messages
    assert "currículo de origem" in messages[-1]


def test_optimization_handles_curriculum_creation_failure(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        curricula,
        _resume_match,
        _ats,
    ) = _page()

    page.current_application_id = 300
    page._optimization_source_curriculum_id = 100
    curricula.create_result = None

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    state = ResumeOptimizationViewState(
        application_id=300,
        status="completed",
        title="Otimização",
        message="Concluída",
        success=True,
        version="2",
    )

    page._on_optimization_succeeded(state)

    assert curricula.created == [
        (
            100,
            "2",
        )
    ]
    assert curricula.associated == []
    assert messages
    assert "cadastrar a nova versão" in messages[-1]


def test_optimization_handles_association_failure(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        curricula,
        _resume_match,
        _ats,
    ) = _page()

    page.current_application_id = 300
    page._optimization_source_curriculum_id = 100
    curricula.association_result = None

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    state = ResumeOptimizationViewState(
        application_id=300,
        status="completed",
        title="Otimização",
        message="Concluída",
        success=True,
        version="2",
    )

    page._on_optimization_succeeded(state)

    assert curricula.created == [
        (
            100,
            "2",
        )
    ]
    assert curricula.associated == [
        (
            300,
            200,
        )
    ]

    assert messages
    assert "associado" in messages[-1]


def test_refresh_reference_data_ignores_unknown_previous_ids(
    qapp,
) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
    ) = _page()

    page.company_combo.addItem(
        "Empresa removida",
        999,
    )
    page.company_combo.setCurrentIndex(
        page.company_combo.findData(999)
    )

    page.curriculum_combo.addItem(
        "Currículo removido",
        999,
    )
    page.curriculum_combo.setCurrentIndex(
        page.curriculum_combo.findData(999)
    )

    page.current_application_id = 999

    page.refresh_reference_data()
    qapp.processEvents()

    assert page.company_combo.findData(999) == -1
    assert page.curriculum_combo.findData(999) == -1
    assert page.table.rowCount() == 1


def test_refresh_reference_data_can_reselect_application_manually(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
    ) = _page()

    page.current_application_id = 300

    selected_rows: list[int] = []

    original_select_row = page.table.selectRow

    def select_row(row: int) -> None:
        selected_rows.append(row)
        original_select_row(row)

    monkeypatch.setattr(
        page.table,
        "selectRow",
        select_row,
    )

    page.refresh_reference_data()
    qapp.processEvents()

    assert selected_rows
    assert selected_rows[-1] == 0
    assert page.table.item(
        selected_rows[-1],
        0,
    ).text() == "300"


def test_refresh_reference_data_skips_empty_table_item(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
    ) = _page()

    page.current_application_id = 300

    def fake_load_applications() -> None:
        page.table.clearContents()
        page.table.clearSelection()
        page.table.setRowCount(2)
        page.table.setItem(
            1,
            0,
            QTableWidgetItem("300"),
        )

    monkeypatch.setattr(
        page,
        "_load_applications",
        fake_load_applications,
    )

    page.refresh_reference_data()
    qapp.processEvents()

    selected_rows = page.table.selectionModel().selectedRows()

    assert len(selected_rows) == 1
    assert selected_rows[0].row() == 1
    assert page.table.item(0, 0) is None
    assert page.table.item(1, 0).text() == "300"