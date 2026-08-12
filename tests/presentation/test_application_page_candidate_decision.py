"""Candidate Decision integration tests for ApplicationPage."""

from __future__ import annotations

import inspect

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QTableWidgetItem

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.structured_resume_quality_validation import (
    StructuredResumeQualityCategory,
    StructuredResumeQualityIssue,
    StructuredResumeQualitySeverity,
)
from acd.presentation.candidate_decision_panel import CandidateDecisionPanel
from acd.presentation.models.candidate_decision_view_state import CandidateDecisionViewState
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
from acd.presentation.models.resume_version_review_view_state import (
    ResumeVersionItemViewState,
    ResumeVersionReviewViewState,
)
from acd.presentation.models.structured_resume_generation_view_state import (
    StructuredResumeGenerationViewState,
)
from acd.presentation.models.structured_resume_quality_validation_view_state import (
    StructuredResumeQualityValidationViewState,
)
from acd.presentation.pages.application_page import ApplicationPage


class _ApplicationService:
    def list_applications(self) -> list[object]:
        return []


class _CompanyService:
    def list_companies(self) -> list[object]:
        return []


class _JobService:
    pass


class _CandidateDecisionViewModel:
    def __init__(self, state: CandidateDecisionViewState) -> None:
        self.state = state
        self.application_ids: list[int] = []

    def load(self, application_id: int) -> CandidateDecisionViewState:
        self.application_ids.append(application_id)
        return self.state


class _ResumeVersionReviewViewModel:
    def __init__(self) -> None:
        self.load_ids: list[int] = []
        self.selected_ids: list[tuple[int, int]] = []

    def load(self, application_id: int) -> ResumeVersionReviewViewState:
        self.load_ids.append(application_id)
        return ResumeVersionReviewViewState(
            status="success",
            title="Versões deste currículo",
            message="",
            application_id=application_id,
            original_content=f"Original {application_id}",
            versions=(ResumeVersionItemViewState(application_id, f"v{application_id}"),),
            selected_version_id=application_id,
            selected_content=f"Versão {application_id}",
        )

    def select_version(
        self,
        application_id: int,
        version_id: int,
    ) -> ResumeVersionReviewViewState:
        self.selected_ids.append((application_id, version_id))
        return self.load(application_id)


class _OptimizedResumeEvaluationViewModel:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int | None]] = []

    def evaluate(
        self,
        application_id: int,
        resume_version_id: int | None,
    ) -> OptimizedResumeEvaluationViewState:
        self.calls.append((application_id, resume_version_id))
        return OptimizedResumeEvaluationViewState(
            status="success",
            title="Avaliação atual da versão selecionada",
            message="Este resultado não foi salvo no histórico.",
            application_id=application_id,
            resume_version_id=resume_version_id,
            original_score=60.0,
            optimized_score=70.0,
            score_delta=10.0,
        )


class _ResumeAdoptionViewModel:
    def __init__(self, source: ApplicationResumeSource = ApplicationResumeSource.RESUME_VERSION) -> None:
        self.source = source
        self.adopt_calls: list[tuple[int, int]] = []
        self.original_calls: list[int] = []

    def adopt(self, application_id: int, version_id: int) -> ResumeAdoptionViewState:
        self.adopt_calls.append((application_id, version_id))
        return ResumeAdoptionViewState("success", application_id, self.source, version_id, "Atualizado", "ok")

    def use_original(self, application_id: int) -> ResumeAdoptionViewState:
        self.original_calls.append(application_id)
        return ResumeAdoptionViewState("success", application_id, ApplicationResumeSource.ORIGINAL, None, "Atualizado", "ok")


class _EffectiveApplicationResumeViewModel:
    def __init__(self) -> None:
        self.load_ids: list[int] = []

    def load(self, application_id: int) -> EffectiveApplicationResumeViewState:
        self.load_ids.append(application_id)
        return EffectiveApplicationResumeViewState(
            "success",
            application_id,
            "Currículo original",
            "",
            "Currículo original",
            f"Efetivo {application_id}",
            "plain_text",
            "ok",
            True,
            True,
            False,
        )


class _SynchronousExecutor(QObject):
    """Test double that exercises page callbacks without a Qt thread lifecycle."""

    started = Signal()
    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()

    @property
    def is_running(self) -> bool:
        return False

    def execute(self, task) -> None:
        self.started.emit()
        try:
            self.succeeded.emit(task())
        except Exception as error:  # pragma: no cover - defensive parity with executor
            self.failed.emit(error)
        finally:
            self.finished.emit()


class _DeferredExecutor(QObject):
    """Synchronous test double that retains one task until the test completes it."""

    started = Signal()
    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()

    def __init__(self, *, raise_on_execute: bool = False) -> None:
        super().__init__()
        self.raise_on_execute = raise_on_execute
        self.execute_calls = 0
        self.task = None

    @property
    def is_running(self) -> bool:
        return self.task is not None

    def execute(self, task) -> None:
        self.execute_calls += 1
        if self.raise_on_execute:
            raise RuntimeError("executor unavailable")
        self.task = task
        self.started.emit()

    def succeed(self) -> None:
        assert self.task is not None
        task = self.task
        self.succeeded.emit(task())
        self._finish()

    def fail(self, error: Exception) -> None:
        self.failed.emit(error)
        self._finish()

    def _finish(self) -> None:
        self.task = None
        self.finished.emit()


class _StructuredResumeGenerationViewModel:
    def __init__(
        self,
        state: StructuredResumeGenerationViewState | None = None,
        error: Exception | None = None,
    ) -> None:
        self.state = state or StructuredResumeGenerationViewState(
            42,
            "success",
            "Versão estruturada gerada",
            "Pronta para revisão.",
            True,
            7,
            "v7",
        )
        self.error = error
        self.application_ids: list[int] = []

    def generate(self, application_id: int) -> StructuredResumeGenerationViewState:
        self.application_ids.append(application_id)
        if self.error is not None:
            raise self.error
        return self.state


class _DocxExportViewModel:
    def __init__(self, state: EffectiveStructuredResumeDocxExportViewState) -> None:
        self.state = state
        self.calls: list[tuple[int, str]] = []

    def export(self, application_id: int, destination_path: str) -> EffectiveStructuredResumeDocxExportViewState:
        self.calls.append((application_id, destination_path))
        return self.state


class _QualityValidationViewModel:
    def __init__(self, state: StructuredResumeQualityValidationViewState) -> None:
        self.state = state
        self.calls: list[int] = []

    def validate(self, application_id: int) -> StructuredResumeQualityValidationViewState:
        self.calls.append(application_id)
        return self.state


def _state(decision: str = "APPLY") -> CandidateDecisionViewState:
    return CandidateDecisionViewState(
        decision=decision,
        score=72.0,
        confidence="MEDIUM",
        headline="Apply",
        summary="The application has sufficient persisted evidence.",
        reasons=(),
        strengths=(),
        risks=(),
        gaps=(),
        recommendations=(),
    )


def _page(
    monkeypatch,
    view_model: _CandidateDecisionViewModel,
    on_action=None,
    structured_resume_generation_view_model: _StructuredResumeGenerationViewModel | None = None,
    effective_structured_resume_docx_export_view_model: _DocxExportViewModel | None = None,
    structured_resume_quality_validation_view_model: _QualityValidationViewModel | None = None,
) -> ApplicationPage:
    return ApplicationPage(
        view_model,
        on_action,
        structured_resume_generation_view_model=structured_resume_generation_view_model,  # type: ignore[arg-type]
        effective_structured_resume_docx_export_view_model=effective_structured_resume_docx_export_view_model,  # type: ignore[arg-type]
        structured_resume_quality_validation_view_model=structured_resume_quality_validation_view_model,  # type: ignore[arg-type]
    )


def _deferred_executor(page: ApplicationPage) -> _DeferredExecutor:
    executor = _DeferredExecutor()
    executor.started.connect(page._on_long_running_task_started)
    executor.succeeded.connect(page._on_long_running_task_succeeded)
    executor.failed.connect(page._on_long_running_task_failed)
    executor.finished.connect(page._on_long_running_task_finished)
    page._resume_optimization_executor = executor  # type: ignore[assignment]
    return executor


def test_quality_validation_button_is_disabled_without_view_model(qapp, monkeypatch) -> None:
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))

    assert page.validate_structured_resume_quality_button.text() == "Validar qualidade do currículo"
    assert not page.validate_structured_resume_quality_button.isEnabled()


def test_application_page_loads_decision_for_selected_application(qapp, monkeypatch) -> None:
    """The selected application ID is forwarded to the injected ViewModel."""
    view_model = _CandidateDecisionViewModel(_state())
    page = _page(monkeypatch, view_model)
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))

    page.table.selectRow(0)

    assert view_model.application_ids == [42]
    assert page.candidate_decision_panel.decision_label.text() == "APPLY"


def test_application_page_refreshes_decision_when_selection_changes(qapp, monkeypatch) -> None:
    """The existing selection cycle refreshes the decision exactly once per ID."""
    view_model = _CandidateDecisionViewModel(_state("INSUFFICIENT_DATA"))
    page = _page(monkeypatch, view_model)
    page.table.setRowCount(2)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.setItem(1, 0, QTableWidgetItem("84"))

    page.table.selectRow(0)
    page.table.selectRow(1)

    assert view_model.application_ids == [42, 84]
    assert page.candidate_decision_panel.decision_label.text() == "INSUFFICIENT_DATA"


def test_application_page_does_not_load_without_application_id(qapp, monkeypatch) -> None:
    """The empty state does not trigger Candidate Decision retrieval."""
    view_model = _CandidateDecisionViewModel(_state())
    page = _page(monkeypatch, view_model)

    page._load_candidate_decision()

    assert view_model.application_ids == []
    assert not page.candidate_decision_panel.empty_state_label.isHidden()


def test_application_page_forwards_only_explicit_action(qapp, monkeypatch) -> None:
    actions: list[str] = []
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()), actions.append)
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))

    page.table.selectRow(0)
    button = page.candidate_decision_panel.actions_layout.itemAt(0).widget()
    assert button is not None
    assert actions == []

    button.click()

    assert actions == ["review_gaps"]


def test_application_page_scrolls_long_candidate_decision_content(qapp, monkeypatch) -> None:
    """Long persisted evidence remains reachable without expanding the viewport."""
    long_text = "evidência " * 120
    view_model = _CandidateDecisionViewModel(
        CandidateDecisionViewState(
            decision="APPLY",
            score=72.0,
            confidence="MEDIUM",
            headline=long_text,
            summary=long_text,
            reasons=(long_text,) * 3,
            strengths=(long_text,) * 3,
            risks=(long_text,) * 3,
            gaps=(long_text,) * 3,
            recommendations=(long_text,) * 3,
        )
    )
    page = _page(monkeypatch, view_model)
    page.resize(800, 600)
    page.show()
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))

    page.table.selectRow(0)
    qapp.processEvents()

    assert page.scroll_area.verticalScrollBar().maximum() > 0
    assert page.candidate_decision_panel.height() > 0


class _FailingResumeAdoptionViewModel:
    def __init__(self) -> None:
        self.calls = 0

    def adopt(self, application_id: int, version_id: int) -> ResumeAdoptionViewState:
        self.calls += 1
        raise RuntimeError("persistence failed")


def test_application_page_keeps_candidate_decision_boundary() -> None:
    """The page depends only on the Presentation ViewModel and panel."""
    source = inspect.getsource(ApplicationPage)

    for forbidden_name in (
        "CandidateDecisionUseCase",
        "CandidateDecisionService",
        "DependencyContainer",
        ".resolve(",
        "acd.infrastructure",
    ):
        assert forbidden_name not in source

    panel_source = inspect.getsource(CandidateDecisionPanel)
    for forbidden_name in (
        "CandidateDecisionUseCase",
        "CandidateDecisionService",
        "DependencyContainer",
        ".resolve(",
        "acd.infrastructure",
    ):
        assert forbidden_name not in panel_source


def test_application_page_clears_and_reloads_review_when_selection_changes(
    qapp,
    monkeypatch,
) -> None:
    review_view_model = _ResumeVersionReviewViewModel()
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_version_review_view_model = review_view_model  # type: ignore[assignment]
    page.table.setRowCount(2)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.setItem(1, 0, QTableWidgetItem("84"))

    page.table.selectRow(0)
    page.table.selectRow(1)

    assert review_view_model.load_ids == [42, 84]
    assert page.resume_version_review_panel.original_content.toPlainText() == "Original 84"
    assert page.resume_version_review_panel.selected_content.toPlainText() == "Versão 84"


def test_application_page_review_selection_only_calls_injected_view_model(
    qapp,
    monkeypatch,
) -> None:
    review_view_model = _ResumeVersionReviewViewModel()
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_version_review_view_model = review_view_model  # type: ignore[assignment]
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))

    page.table.selectRow(0)
    page.resume_version_review_panel.version_selector.setCurrentIndex(0)

    assert review_view_model.selected_ids == []


def test_application_page_evaluates_only_after_explicit_panel_click(qapp, monkeypatch) -> None:
    review_view_model = _ResumeVersionReviewViewModel()
    evaluation_view_model = _OptimizedResumeEvaluationViewModel()
    monkeypatch.setattr(
        "acd.presentation.pages.application_page.LongRunningTaskExecutor",
        _SynchronousExecutor,
    )
    page = ApplicationPage(
        _CandidateDecisionViewModel(_state()),
        resume_version_review_view_model=review_view_model,  # type: ignore[arg-type]
        optimized_resume_evaluation_view_model=evaluation_view_model,  # type: ignore[arg-type]
    )
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)

    assert evaluation_view_model.calls == []
    page.resume_version_review_panel.evaluate_button.click()

    assert evaluation_view_model.calls == [(42, 42)]
    assert "não foi salvo" in page.resume_version_review_panel.evaluation_label.text()


def test_application_page_adopts_only_after_explicit_panel_click(qapp, monkeypatch) -> None:
    review = _ResumeVersionReviewViewModel()
    adoption = _ResumeAdoptionViewModel()
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page._resume_adoption_view_model = adoption  # type: ignore[assignment]
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    page.resume_version_review_panel.adopt_button.click()

    assert adoption.adopt_calls == [(42, 42)]
    assert "v42" in page.resume_version_review_panel.adopted_source_label.text()


def test_application_page_returns_to_original_after_explicit_click(qapp, monkeypatch) -> None:
    review = _ResumeVersionReviewViewModel()
    adoption = _ResumeAdoptionViewModel()
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page._resume_adoption_view_model = adoption  # type: ignore[assignment]
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    page.resume_version_review_panel.adopt_button.click()
    page.resume_version_review_panel.use_original_button.click()

    assert adoption.original_calls == [42]
    assert "Original" in page.resume_version_review_panel.adopted_source_label.text()


def test_application_page_ignores_adoption_without_a_current_application(qapp, monkeypatch) -> None:
    adoption = _ResumeAdoptionViewModel()
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_adoption_view_model = adoption  # type: ignore[assignment]

    page._adopt_resume_version(42)
    page._use_original_resume()

    assert adoption.adopt_calls == []
    assert adoption.original_calls == []


def test_application_page_preserves_adoption_state_when_view_model_raises(qapp, monkeypatch) -> None:
    review = _ResumeVersionReviewViewModel()
    failing = _FailingResumeAdoptionViewModel()
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page._resume_adoption_view_model = failing  # type: ignore[assignment]
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)

    page.resume_version_review_panel.adopt_button.click()

    assert failing.calls == 1
    assert "Original" in page.resume_version_review_panel.adopted_source_label.text()
    assert "Não foi possível" in page.resume_version_review_panel.adoption_message_label.text()


def test_application_page_ignores_stale_optimized_evaluation_after_application_changes(
    qapp, monkeypatch
) -> None:
    review = _ResumeVersionReviewViewModel()
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page.table.setRowCount(2)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.setItem(1, 0, QTableWidgetItem("84"))
    page.table.selectRow(0)
    page.table.selectRow(1)
    page.resume_version_review_panel.evaluation_label.setText("Estado de B")

    page._on_optimized_evaluation_succeeded(
        OptimizedResumeEvaluationViewState(
            status="success", title="Resultado de A", message="antigo",
            application_id=42, resume_version_id=42,
        )
    )

    assert page.current_application_id == 84
    assert page.resume_version_review_panel.selected_version_id == 84
    assert page.resume_version_review_panel.evaluation_label.text() == "Estado de B"


def test_application_page_preserves_context_when_optimized_evaluation_fails(qapp, monkeypatch) -> None:
    review = _ResumeVersionReviewViewModel()
    adoption = _ResumeAdoptionViewModel()
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page._resume_adoption_view_model = adoption  # type: ignore[assignment]
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    page._optimized_evaluation_request = (42, 42)
    page._on_optimized_evaluation_started()
    page._on_optimized_evaluation_failed(RuntimeError("provider failure"))
    page._on_optimized_evaluation_finished()

    assert page.current_application_id == 42
    assert page.resume_version_review_panel.selected_version_id == 42
    assert not page.resume_version_review_panel._evaluation_running
    assert "Não foi possível avaliar" in page.resume_version_review_panel.evaluation_label.text()
    assert adoption.adopt_calls == []
    assert adoption.original_calls == []


def test_application_page_restores_controls_after_resume_optimization_finishes(qapp, monkeypatch) -> None:
    review = _ResumeVersionReviewViewModel()
    adoption = _ResumeAdoptionViewModel()
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page._resume_adoption_view_model = adoption  # type: ignore[assignment]
    page._resume_optimization_view_model = object()  # type: ignore[assignment]
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)

    page._on_optimization_started()
    assert not page.optimize_resume_button.isEnabled()
    assert "Otimizando" in page.optimization_status_label.text()

    page._on_optimization_finished()

    assert page.optimize_resume_button.isEnabled()
    assert page.current_application_id == 42
    assert page.resume_version_review_panel.selected_version_id == 42
    assert adoption.adopt_calls == []
    assert adoption.original_calls == []


def test_application_page_ignores_stale_resume_optimization_success_after_application_changes(
    qapp, monkeypatch
) -> None:
    review = _ResumeVersionReviewViewModel()
    adoption = _ResumeAdoptionViewModel()
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page._resume_adoption_view_model = adoption  # type: ignore[assignment]
    page._resume_optimization_view_model = object()  # type: ignore[assignment]
    page.table.setRowCount(2)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.setItem(1, 0, QTableWidgetItem("84"))
    page.table.selectRow(0)
    page.table.selectRow(1)
    page.optimization_status_label.setText("Estado de B")

    page._on_optimization_succeeded(
        ResumeOptimizationViewState(42, "success", "Resultado de A", "antigo", True, "vA")
    )
    page._on_optimization_finished()

    assert page.current_application_id == 84
    assert page.optimization_status_label.text() == "Estado de B"
    assert page.resume_version_review_panel.selected_version_id == 84
    assert page.optimize_resume_button.isEnabled()
    assert adoption.adopt_calls == []
    assert adoption.original_calls == []


def test_application_page_loads_effective_resume_without_using_visual_selection(
    qapp, monkeypatch
) -> None:
    review = _ResumeVersionReviewViewModel()
    effective = _EffectiveApplicationResumeViewModel()
    page = ApplicationPage(
        _CandidateDecisionViewModel(_state()),
        resume_version_review_view_model=review,  # type: ignore[arg-type]
        effective_application_resume_view_model=effective,  # type: ignore[arg-type]
    )
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))

    page.table.selectRow(0)
    page._on_resume_version_selected(42)

    assert effective.load_ids == [42]
    assert page.effective_application_resume_preview_panel.content.toPlainText() == "Efetivo 42"


def test_application_page_disables_structured_generation_without_view_model(qapp, monkeypatch) -> None:
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))
    page._resume_optimization_view_model = object()  # type: ignore[assignment]
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)

    assert page.generate_structured_resume_button.text() == "Gerar versão estruturada"
    assert not page.generate_structured_resume_button.isEnabled()
    assert not page.optimize_resume_button.isEnabled()
    assert page._structured_resume_generation_view_model is None


def test_application_page_keeps_textual_and_structured_generation_independent(qapp, monkeypatch) -> None:
    structured = _StructuredResumeGenerationViewModel()
    page = _page(
        monkeypatch,
        _CandidateDecisionViewModel(_state()),
        structured_resume_generation_view_model=structured,
    )
    assert not page.generate_structured_resume_button.isEnabled()
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    executor = _deferred_executor(page)

    assert page.generate_structured_resume_button.isEnabled()
    page.generate_structured_resume_button.click()

    assert executor.execute_calls == 1
    assert structured.application_ids == []
    assert page._active_long_running_task == "structured_resume_generation"
    assert not page.generate_structured_resume_button.isEnabled()
    assert not page.optimize_resume_button.isEnabled()
    assert page.optimization_status_label.text() == "Gerando versão estruturada..."

    page._optimize_resume()
    page._generate_structured_resume_version()
    executor.succeed()

    assert structured.application_ids == [42]
    assert executor.execute_calls == 1
    assert page._active_long_running_task is None
    assert page._structured_resume_generation_application_id is None


def test_application_page_refreshes_only_current_structured_generation(qapp, monkeypatch) -> None:
    review = _ResumeVersionReviewViewModel()
    structured = _StructuredResumeGenerationViewModel()
    adoption = _ResumeAdoptionViewModel()
    page = _page(
        monkeypatch,
        _CandidateDecisionViewModel(_state()),
        structured_resume_generation_view_model=structured,
    )
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page._resume_adoption_view_model = adoption  # type: ignore[assignment]
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    review.load_ids.clear()
    executor = _deferred_executor(page)

    preview = page.effective_application_resume_preview_panel.content.toPlainText()
    selected_version_id = page.resume_version_review_panel.selected_version_id
    page._generate_structured_resume_version()
    executor.succeed()

    assert review.load_ids == [42]
    assert "Versão estruturada gerada" in page.optimization_status_label.text()
    assert page.effective_application_resume_preview_panel.content.toPlainText() == preview
    assert page.resume_version_review_panel.selected_version_id == selected_version_id
    assert adoption.adopt_calls == []
    assert adoption.original_calls == []


def test_application_page_handles_structured_functional_and_technical_failures(qapp, monkeypatch) -> None:
    review = _ResumeVersionReviewViewModel()
    functional = _StructuredResumeGenerationViewModel(
        StructuredResumeGenerationViewState(42, "provider_timeout", "Tempo esgotado", "Tente novamente.", False)
    )
    page = _page(
        monkeypatch,
        _CandidateDecisionViewModel(_state()),
        structured_resume_generation_view_model=functional,
    )
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    review.load_ids.clear()
    executor = _deferred_executor(page)

    page._generate_structured_resume_version()
    executor.succeed()

    assert review.load_ids == []
    assert page.optimization_status_label.text() == "Tempo esgotado: Tente novamente."
    assert page._active_long_running_task is None

    page._generate_structured_resume_version()
    executor.fail(RuntimeError("provider failure"))

    assert "Não foi possível gerar" in page.optimization_status_label.text()
    assert page._active_long_running_task is None
    assert page._structured_resume_generation_application_id is None
    assert page.generate_structured_resume_button.isEnabled()


def test_application_page_ignores_stale_structured_success_and_failure(qapp, monkeypatch) -> None:
    review = _ResumeVersionReviewViewModel()
    structured = _StructuredResumeGenerationViewModel()
    page = _page(
        monkeypatch,
        _CandidateDecisionViewModel(_state()),
        structured_resume_generation_view_model=structured,
    )
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page.table.setRowCount(2)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.setItem(1, 0, QTableWidgetItem("84"))
    page.table.selectRow(0)
    executor = _deferred_executor(page)

    page._generate_structured_resume_version()
    page.table.selectRow(1)
    review.load_ids.clear()
    page.optimization_status_label.setText("Estado de B")
    executor.succeed()

    assert review.load_ids == []
    assert page.optimization_status_label.text() == "Estado de B"
    assert page.resume_version_review_panel.selected_version_id == 84

    page.table.selectRow(0)
    page._generate_structured_resume_version()
    page.table.selectRow(1)
    page.optimization_status_label.setText("Estado de B")
    executor.fail(RuntimeError("A failed"))

    assert page.optimization_status_label.text() == "Estado de B"
    assert page._active_long_running_task is None
    assert page._structured_resume_generation_application_id is None


def test_application_page_recovers_structured_start_and_refresh_failures(qapp, monkeypatch) -> None:
    structured = _StructuredResumeGenerationViewModel()
    page = _page(
        monkeypatch,
        _CandidateDecisionViewModel(_state()),
        structured_resume_generation_view_model=structured,
    )
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    failing_executor = _DeferredExecutor(raise_on_execute=True)
    failing_executor.started.connect(page._on_long_running_task_started)
    failing_executor.succeeded.connect(page._on_long_running_task_succeeded)
    failing_executor.failed.connect(page._on_long_running_task_failed)
    failing_executor.finished.connect(page._on_long_running_task_finished)
    page._resume_optimization_executor = failing_executor  # type: ignore[assignment]

    page._generate_structured_resume_version()

    assert page._active_long_running_task is None
    assert page._structured_resume_generation_application_id is None
    assert page.generate_structured_resume_button.isEnabled()
    assert "Não foi possível gerar" in page.optimization_status_label.text()

    executor = _deferred_executor(page)
    monkeypatch.setattr(page, "_load_resume_version_review", lambda: (_ for _ in ()).throw(RuntimeError()))
    page._generate_structured_resume_version()
    executor.succeed()

    assert "não foi possível atualizar o histórico" in page.optimization_status_label.text().lower()
    assert page._active_long_running_task is None


def test_application_page_handles_unexpected_structured_result_without_side_effects(qapp, monkeypatch) -> None:
    review = _ResumeVersionReviewViewModel()
    page = _page(
        monkeypatch,
        _CandidateDecisionViewModel(_state()),
        structured_resume_generation_view_model=_StructuredResumeGenerationViewModel(),
    )
    page._resume_version_review_view_model = review  # type: ignore[assignment]
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    review.load_ids.clear()
    executor = _deferred_executor(page)

    page._generate_structured_resume_version()
    executor.succeeded.emit(object())
    executor._finish()

    assert review.load_ids == []
    assert "Não foi possível gerar" in page.optimization_status_label.text()
    assert page._active_long_running_task is None


def test_application_page_disables_docx_export_without_view_model(qapp, monkeypatch) -> None:
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()))

    assert page.export_effective_resume_docx_button.text() == "Exportar currículo em DOCX"
    assert not page.export_effective_resume_docx_button.isEnabled()
    assert page.export_effective_resume_docx_button.toolTip()


def test_application_page_docx_export_cancellation_does_not_start_task(qapp, monkeypatch) -> None:
    view_model = _DocxExportViewModel(
        EffectiveStructuredResumeDocxExportViewState("success", 42, True, "resume.docx", "original", "ok")
    )
    page = _page(
        monkeypatch, _CandidateDecisionViewModel(_state()),
        effective_structured_resume_docx_export_view_model=view_model,
    )
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    monkeypatch.setattr(
        "acd.presentation.pages.application_page.QFileDialog.getSaveFileName", lambda *args: ("", "")
    )

    page.export_effective_resume_docx_button.click()

    assert view_model.calls == []
    assert page._active_long_running_task is None


def test_application_page_runs_docx_export_through_existing_executor(qapp, monkeypatch) -> None:
    view_model = _DocxExportViewModel(
        EffectiveStructuredResumeDocxExportViewState("success", 42, True, "Currículo espaço.docx", "original", "Exportado.")
    )
    page = _page(
        monkeypatch, _CandidateDecisionViewModel(_state()),
        effective_structured_resume_docx_export_view_model=view_model,
    )
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    executor = _deferred_executor(page)
    dialog_calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        "acd.presentation.pages.application_page.QFileDialog.getSaveFileName",
        lambda *args: (dialog_calls.append(args) or ("Currículo espaço", "")),
    )

    page.export_effective_resume_docx_button.click()

    assert dialog_calls[0][3] == "Documentos do Word (*.docx)"
    assert page._active_long_running_task == "effective_resume_docx_export"
    assert page.export_effective_resume_docx_button.text() == "Exportando..."
    assert not page.optimize_resume_button.isEnabled()
    assert not page.generate_structured_resume_button.isEnabled()
    page.export_effective_resume_docx_button.click()
    executor.succeed()

    assert view_model.calls == [(42, "Currículo espaço.docx")]
    assert executor.execute_calls == 1
    assert page._active_long_running_task is None
    assert page.export_effective_resume_docx_button.text() == "Exportar currículo em DOCX"
    assert page.optimization_status_label.text() == "Exportado."


def test_application_page_ignores_stale_docx_export_failure(qapp, monkeypatch) -> None:
    view_model = _DocxExportViewModel(
        EffectiveStructuredResumeDocxExportViewState("export_failed", 42, False, "resume.docx", "original", "Falha A")
    )
    page = _page(
        monkeypatch, _CandidateDecisionViewModel(_state()),
        effective_structured_resume_docx_export_view_model=view_model,
    )
    page.table.setRowCount(2)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.setItem(1, 0, QTableWidgetItem("84"))
    page.table.selectRow(0)
    executor = _deferred_executor(page)
    monkeypatch.setattr(
        "acd.presentation.pages.application_page.QFileDialog.getSaveFileName", lambda *args: ("resume.docx", "")
    )
    page.export_effective_resume_docx_button.click()
    page.table.selectRow(1)
    page.optimization_status_label.setText("Estado de B")
    executor.succeed()

    assert page.optimization_status_label.text() == "Estado de B"
    assert page._active_long_running_task is None


def test_application_page_runs_quality_validation_and_renders_issues(qapp, monkeypatch) -> None:
    issue = StructuredResumeQualityIssue("SKILL_EMPTY", StructuredResumeQualitySeverity.WARNING, StructuredResumeQualityCategory.SKILLS, "skills[0]", "value", "Competência vazia.", "Informe a competência.")
    view_model = _QualityValidationViewModel(StructuredResumeQualityValidationViewState("success", 42, True, True, 95, (issue,), 0, 1, 0, "1 alerta.", "Validação concluída com pontos de atenção."))
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()), structured_resume_quality_validation_view_model=view_model)
    page.table.setRowCount(1)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.selectRow(0)
    executor = _deferred_executor(page)

    page.validate_structured_resume_quality_button.click()
    assert page._active_long_running_task == "structured_resume_quality_validation"
    assert page.validate_structured_resume_quality_button.text() == "Validando..."
    executor.succeed()

    assert view_model.calls == [42]
    assert "Score: 95" in page.structured_resume_quality_label.text()
    assert "Recomendação: Informe a competência." in page.structured_resume_quality_issues.toPlainText()


def test_application_page_ignores_stale_quality_validation_result(qapp, monkeypatch) -> None:
    view_model = _QualityValidationViewModel(StructuredResumeQualityValidationViewState("success", 42, True, True, 100, (), 0, 0, 0, "Sem issues.", "Resultado A"))
    page = _page(monkeypatch, _CandidateDecisionViewModel(_state()), structured_resume_quality_validation_view_model=view_model)
    page.table.setRowCount(2)
    page.table.setItem(0, 0, QTableWidgetItem("42"))
    page.table.setItem(1, 0, QTableWidgetItem("84"))
    page.table.selectRow(0)
    executor = _deferred_executor(page)
    page.validate_structured_resume_quality_button.click()
    page.table.selectRow(1)
    page.structured_resume_quality_label.setText("Estado de B")
    executor.succeed()

    assert page.structured_resume_quality_label.text() == "Estado de B"
