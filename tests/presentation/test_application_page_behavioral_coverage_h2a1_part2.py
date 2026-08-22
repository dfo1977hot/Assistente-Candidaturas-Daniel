from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtWidgets import QMessageBox, QProgressDialog

from acd.presentation.models.resume_optimization_view_state import (
    ResumeOptimizationViewState,
)
from acd.presentation.pages.application_page import ApplicationPage
from acd.services.assisted_application_service import AssistedApplicationResult


class _ApplicationService:
    def __init__(self) -> None:
        self.application = SimpleNamespace(
            id=300,
            job_id=10,
        )

    def list_applications(self):
        return []

    def search_applications(self, query: str):
        del query
        return []

    def filter_applications(self, **filters):
        del filters
        return []

    def get_application(self, application_id: int):
        if application_id == 300:
            return self.application
        return None


class _CompanyService:
    def list_companies(self):
        return []


class _JobService:
    def __init__(self) -> None:
        self.job = SimpleNamespace(
            id=10,
            application_url="https://example.com/apply",
            job_url="https://example.com/job",
        )

    def filter_jobs(self, **filters):
        del filters
        return []

    def get_job(self, job_id: int):
        if job_id == 10:
            return self.job
        return None


class _CurriculumService:
    def __init__(self) -> None:
        self.curricula = [
            SimpleNamespace(
                id=100,
                name="Currículo Origem",
                version="1",
            ),
            SimpleNamespace(
                id=200,
                name="Currículo Otimizado",
                version="2",
            ),
        ]
        self.created = []
        self.associated = []

    def list_curricula(self):
        return list(self.curricula)

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
        return self.curricula[1]

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
        return SimpleNamespace(id=1)


class _ResumeMatchService:
    def analyze(self, *, application, curriculum):
        del application, curriculum
        return None

    def get_cached(self, application_id, curriculum_id):
        del application_id, curriculum_id
        return None


class _ProfileStore:
    def __init__(self) -> None:
        self.profile = SimpleNamespace(
            full_name="Daniel Oliveira",
            email="daniel@example.com",
        )

    def load(self):
        return self.profile


class _AssistedApplicationService:
    def __init__(self) -> None:
        self.profile_store = _ProfileStore()
        self.calls = []

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
        progress((50, "Preparando candidatura"))
        return None


class _Executor:
    def __init__(self) -> None:
        self.tasks = []
        self.is_running = False

    def execute_with_context(self, task):
        self.tasks.append(task)

        class _Token:
            is_cancellation_requested = False

        return task(
            lambda payload: setattr(
                self,
                "last_progress",
                payload,
            ),
            _Token(),
        )


class _OptimizationViewModel:
    def __init__(self, state) -> None:
        self.state = state
        self.calls = []

    def optimize(self, application_id: int):
        self.calls.append(application_id)
        return self.state


def _page(
    *,
    assisted_application_service=None,
    optimization_view_model=None,
):
    application_service = _ApplicationService()
    curriculum_service = _CurriculumService()

    page = ApplicationPage(
        application_service=application_service,  # type: ignore[arg-type]
        company_service=_CompanyService(),  # type: ignore[arg-type]
        job_service=_JobService(),  # type: ignore[arg-type]
        curriculum_service=curriculum_service,  # type: ignore[arg-type]
        resume_match_service=_ResumeMatchService(),  # type: ignore[arg-type]
        assisted_application_service=assisted_application_service,  # type: ignore[arg-type]
        resume_optimization_view_model=optimization_view_model,  # type: ignore[arg-type]
    )

    return page, application_service, curriculum_service


def test_assisted_application_requires_selection(
    qapp,
    monkeypatch,
) -> None:
    assisted = _AssistedApplicationService()
    page, _applications, _curricula = _page(
        assisted_application_service=assisted,
    )

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._prepare_assisted_application()

    assert messages == ["Selecione uma candidatura."]
    assert assisted.calls == []


def test_assisted_application_requires_existing_application(
    qapp,
    monkeypatch,
) -> None:
    assisted = _AssistedApplicationService()
    page, applications, _curricula = _page(
        assisted_application_service=assisted,
    )

    page.current_application_id = 999

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._prepare_assisted_application()

    assert messages == ["Candidatura não encontrada."]
    assert applications.get_application(999) is None


def test_assisted_application_requires_job_url(
    qapp,
    monkeypatch,
) -> None:
    assisted = _AssistedApplicationService()
    page, _applications, _curricula = _page(
        assisted_application_service=assisted,
    )

    page.current_application_id = 300
    page.job_service.job.application_url = ""
    page.job_service.job.job_url = ""

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._prepare_assisted_application()

    assert messages == [
        "Cadastre a URL da candidatura ou a URL da vaga antes de continuar."
    ]


def test_assisted_application_progress_callback(qapp) -> None:
    assisted = _AssistedApplicationService()
    page, _applications, _curricula = _page(
        assisted_application_service=assisted,
    )

    page._on_assisted_application_progress(
        (
            20,
            "Preparando",
        )
    )

    page._assisted_application_progress = QProgressDialog(
        "",
        "",
        0,
        100,
        page,
    )

    page._on_assisted_application_progress(
        (
            70,
            "Preenchendo formulário",
        )
    )

    assert page._assisted_application_progress.value() == 70
    assert (
        page._assisted_application_progress.labelText()
        == "Preenchendo formulário"
    )


def test_assisted_application_success_marks_application_as_sent(
    qapp,
    monkeypatch,
) -> None:
    assisted = _AssistedApplicationService()
    page, _applications, _curricula = _page(
        assisted_application_service=assisted,
    )

    page.current_application_id = 300

    saved: list[bool] = []

    monkeypatch.setattr(
        page,
        "_save_application",
        lambda: saved.append(True),
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    result = AssistedApplicationResult(
        platform="LinkedIn",
        url="https://example.com/apply",
        fields_filled=8,
        resume_attached=True,
        linkedin_restricted_mode=True,
    )

    page._on_assisted_application_succeeded(result)

    assert page.status_combo.currentText() == "Aplicada"
    assert saved == [True]


def test_assisted_application_success_ignores_unexpected_result(
    qapp,
) -> None:
    assisted = _AssistedApplicationService()
    page, _applications, _curricula = _page(
        assisted_application_service=assisted,
    )

    page._assisted_application_progress = QProgressDialog(
        "",
        "",
        0,
        100,
        page,
    )

    page._on_assisted_application_succeeded(
        object()
    )

    assert page._assisted_application_progress is None
    assert page.assisted_application_button.isEnabled()


def test_assisted_application_failure_restores_ui(
    qapp,
    monkeypatch,
) -> None:
    assisted = _AssistedApplicationService()
    page, _applications, _curricula = _page(
        assisted_application_service=assisted,
    )

    page._assisted_application_progress = QProgressDialog(
        "",
        "",
        0,
        100,
        page,
    )

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._on_assisted_application_failed(
        RuntimeError("Falha simulada")
    )

    assert page._assisted_application_progress is None
    assert page.assisted_application_button.isEnabled()
    assert messages == ["Falha simulada"]


def test_optimization_requires_selected_curriculum(
    qapp,
    monkeypatch,
) -> None:
    state = ResumeOptimizationViewState(
        application_id=300,
        status="completed",
        success=True,
        title="Otimização",
        message="Concluída",
        version="2",
    )
    view_model = _OptimizationViewModel(state)

    page, _applications, _curricula = _page(
        optimization_view_model=view_model,
    )

    page.current_application_id = 300

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page.curriculum_combo.setCurrentIndex(0)
    page._optimize_resume()

    assert messages == [
        "Selecione um currículo no campo Currículo antes de continuar."
    ]
    assert view_model.calls == []


def test_optimization_progress_accepts_tuple_dict_and_integer(
    qapp,
) -> None:
    state = ResumeOptimizationViewState(
        application_id=300,
        status="completed",
        success=True,
        title="Otimização",
        message="Concluída",
        version="2",
    )
    view_model = _OptimizationViewModel(state)

    page, _applications, _curricula = _page(
        optimization_view_model=view_model,
    )

    page._active_long_running_task = "optimization"
    page._show_optimization_progress()

    dialog = page._optimization_progress_dialog

    assert dialog is not None

    page._on_optimization_progress(
        (
            20,
            "Preparando",
        )
    )
    assert dialog.value() == 20
    assert dialog.labelText() == "Preparando"

    page._on_optimization_progress(
        {
            "value": 45,
            "message": "Gerando",
        }
    )
    assert dialog.value() == 45
    assert dialog.labelText() == "Gerando"

    page._on_optimization_progress(150)
    assert dialog.value() == 100

    page._on_optimization_progress(-10)
    assert dialog.value() == 0


def test_optimization_progress_ignores_wrong_state(
    qapp,
) -> None:
    page, _applications, _curricula = _page()

    page._on_optimization_progress(
        (
            50,
            "Ignorado",
        )
    )

    page._active_long_running_task = "other"
    page._show_optimization_progress()

    dialog = page._optimization_progress_dialog

    assert dialog is not None

    page._on_optimization_progress(
        (
            80,
            "Também ignorado",
        )
    )

    assert dialog.value() == 0


def test_optimization_success_with_existing_optimized_curriculum(
    qapp,
    monkeypatch,
) -> None:
    state = ResumeOptimizationViewState(
        application_id=300,
        status="completed",
        success=True,
        title="Otimização concluída",
        message="Currículo otimizado",
        version="2",
    )

    page, _applications, curricula = _page()

    page.current_application_id = 300

    callback_ids: list[int] = []
    page._on_optimized_curriculum_created_callback = callback_ids.append

    monkeypatch.setattr(
        page,
        "refresh_reference_data",
        lambda: None,
    )

    page._on_optimization_succeeded(
        (
            state,
            curricula.curricula[1],
        )
    )

    assert page.curriculum_combo.currentData() == 200
    assert "nova versão otimizada" in page.resume_match_label.text()
    assert "Currículo Otimizado" in page.optimization_status_label.text()
    assert callback_ids == [200]


def test_optimization_failure_state_shows_warning(
    qapp,
    monkeypatch,
) -> None:
    state = ResumeOptimizationViewState(
        application_id=300,
        status="failed",
        success=False,
        title="Otimização",
        message="Não foi possível otimizar",
        version=None,
    )

    page, _applications, _curricula = _page()
    page.current_application_id = 300

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._on_optimization_succeeded(state)

    assert warnings == ["Não foi possível otimizar"]
    assert "Não foi possível otimizar" in (
        page.optimization_status_label.text()
    )


def test_optimization_unexpected_result_is_handled(
    qapp,
    monkeypatch,
) -> None:
    page, _applications, _curricula = _page()

    critical: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: critical.append(
            str(message)
        ),
    )

    page._on_optimization_succeeded(
        object()
    )

    assert critical
    assert "resultado inesperado" in critical[-1]


def test_optimization_failed_and_finished_restore_state(
    qapp,
    monkeypatch,
) -> None:
    state = ResumeOptimizationViewState(
        application_id=300,
        status="completed",
        success=True,
        title="Otimização",
        message="Concluída",
        version="2",
    )
    view_model = _OptimizationViewModel(state)

    page, _applications, _curricula = _page(
        optimization_view_model=view_model,
    )

    page.current_application_id = 300

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._show_optimization_progress()
    page._optimization_source_curriculum_id = 100

    page._on_optimization_failed(
        RuntimeError("Falha controlada")
    )

    assert "Falha controlada" in messages[-1]
    assert "Falha controlada" in (
        page.optimization_status_label.text()
    )

    page._on_optimization_finished()

    assert page._optimization_progress_dialog is None
    assert page._optimization_source_curriculum_id is None
    assert page.optimize_resume_button.isEnabled()