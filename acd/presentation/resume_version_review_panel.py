"""Passive Qt panel for comparing a curriculum with its generated versions."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from acd.application.application_resume_source import ApplicationResumeSource
from acd.presentation.models.optimized_resume_evaluation_view_state import (
    OptimizedResumeEvaluationViewState,
)
from acd.presentation.models.resume_adoption_view_state import ResumeAdoptionViewState
from acd.presentation.models.resume_version_review_view_state import (
    ResumeVersionReviewViewState,
)


class ResumeVersionReviewPanel(QWidget):
    """Render supplied review state and emit visual-only version selections."""

    version_selected = Signal(int)
    evaluation_requested = Signal(int)
    adopt_version_requested = Signal(int)
    use_original_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        group = QGroupBox("Versões deste currículo")
        group_layout = QVBoxLayout(group)

        self.message_label = QLabel("Selecione uma candidatura para visualizar as versões.")
        self.message_label.setWordWrap(True)
        group_layout.addWidget(self.message_label)

        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        self.version_selector = QComboBox()
        self.version_selector.currentIndexChanged.connect(self._emit_selected_version)
        details_layout.addWidget(self.version_selector)

        content_layout = QHBoxLayout()
        self.original_content = self._create_read_only_content("ORIGINAL", content_layout)
        self.selected_content = self._create_read_only_content(
            "VERSÃO SELECIONADA",
            content_layout,
        )
        details_layout.addLayout(content_layout)
        self.explanation_label = QLabel()
        self.explanation_label.setWordWrap(True)
        details_layout.addWidget(self.explanation_label)
        self.adopted_source_label = QLabel()
        self.adopted_source_label.setWordWrap(True)
        details_layout.addWidget(self.adopted_source_label)
        self.adoption_message_label = QLabel()
        self.adoption_message_label.setWordWrap(True)
        details_layout.addWidget(self.adoption_message_label)
        self.adopt_button = QPushButton("Usar esta versão nesta candidatura")
        self.adopt_button.clicked.connect(self._request_adoption)
        details_layout.addWidget(self.adopt_button)
        self.use_original_button = QPushButton("Usar currículo original")
        self.use_original_button.clicked.connect(self._request_original)
        details_layout.addWidget(self.use_original_button)
        self.evaluate_button = QPushButton("Avaliar versão otimizada")
        self.evaluate_button.clicked.connect(self._request_evaluation)
        details_layout.addWidget(self.evaluate_button)
        self.evaluation_label = QLabel()
        self.evaluation_label.setWordWrap(True)
        details_layout.addWidget(self.evaluation_label)
        self._evaluation_available = False
        self._evaluation_running = False
        self._adoption_state: ResumeAdoptionViewState | None = None
        self._visualized_version_id: int | None = None
        self._adoption_running = False

        group_layout.addWidget(self.details_widget)
        layout.addWidget(group)
        self.show_empty_state()

    def render(self, state: ResumeVersionReviewViewState) -> None:
        """Render an immutable ViewModel projection without querying dependencies."""
        self.message_label.setText(state.message)
        self.message_label.setVisible(bool(state.message))
        self.details_widget.setVisible(bool(state.versions))
        self.version_selector.blockSignals(True)
        self.version_selector.clear()
        for version in state.versions:
            self.version_selector.addItem(version.label, version.version_id)
        if state.selected_version_id is not None:
            index = self.version_selector.findData(state.selected_version_id)
            self.version_selector.setCurrentIndex(index)
        self.version_selector.blockSignals(False)
        self.original_content.setPlainText(state.original_content)
        self.selected_content.setPlainText(state.selected_content)
        self.explanation_label.setText(state.explanation)
        self.explanation_label.setVisible(bool(state.explanation))
        self._visualized_version_id = state.selected_version_id
        self._render_source(
            state.resume_source,
            state.selected_resume_version_id,
            state,
            "",
        )
        self.clear_evaluation()
        self._update_evaluation_button()

    def set_evaluation_available(self, available: bool) -> None:
        """Set whether an injected evaluation ViewModel is available."""
        self._evaluation_available = available
        self._update_evaluation_button()

    def set_evaluation_running(self, running: bool) -> None:
        """Render the explicit evaluation loading state."""
        self._evaluation_running = running
        if running:
            self.evaluation_label.setText("Avaliando versão...")
        self._update_evaluation_button()

    def render_evaluation(self, state: OptimizedResumeEvaluationViewState) -> None:
        """Render a transient evaluation belonging to the current selected version."""
        self.evaluation_label.setText(
            f"{state.title}: {state.message}" if state.message else state.title
        )
        if state.status == "success":
            self.evaluation_label.setText(
                f"{state.title}\n"
                f"ATS original: {state.original_score:.1f}\n"
                f"ATS da versão: {state.optimized_score:.1f}\n"
                f"Delta: {state.score_delta:+.1f}\n"
                f"{state.message}"
            )

    def clear_evaluation(self) -> None:
        """Clear any result that may belong to a previously selected version."""
        self.evaluation_label.clear()

    @property
    def selected_version_id(self) -> int | None:
        """Return the currently selected generated version identifier."""
        version_id = self.version_selector.currentData()
        return version_id if isinstance(version_id, int) else None

    def show_empty_state(self) -> None:
        """Clear the projection when no application is selected."""
        self.message_label.setText("Selecione uma candidatura para visualizar as versões.")
        self.message_label.show()
        self.details_widget.hide()
        self.version_selector.blockSignals(True)
        self.version_selector.clear()
        self.version_selector.blockSignals(False)
        self.original_content.clear()
        self.selected_content.clear()
        self.explanation_label.clear()
        self.clear_evaluation()
        self._adoption_state = None
        self._visualized_version_id = None
        self.adopted_source_label.clear()
        self.adoption_message_label.clear()
        self.adopt_button.setEnabled(False)
        self.use_original_button.setEnabled(False)
        self._update_evaluation_button()

    def _emit_selected_version(self, index: int) -> None:
        version_id = self.version_selector.itemData(index)
        if isinstance(version_id, int):
            self._visualized_version_id = version_id
            self.clear_evaluation()
            self.version_selected.emit(version_id)

    def render_adoption(
        self, state: ResumeAdoptionViewState, review: ResumeVersionReviewViewState
    ) -> None:
        """Render an explicit command outcome without querying or writing anything."""
        self._adoption_state = state
        self._adoption_running = False
        self._render_source(
            state.resume_source,
            state.selected_resume_version_id,
            review,
            f"{state.title}: {state.message}",
        )

    def set_adoption_running(self, running: bool) -> None:
        """Temporarily prevent repeated explicit clicks during a local write."""
        self._adoption_running = running
        self._update_adoption_buttons()

    def _render_source(
        self,
        source: ApplicationResumeSource,
        selected_resume_version_id: int | None,
        review: ResumeVersionReviewViewState,
        message: str,
    ) -> None:
        label = "Original"
        if source is ApplicationResumeSource.RESUME_VERSION:
            version = next(
                (item for item in review.versions if item.version_id == selected_resume_version_id),
                None,
            )
            label = version.label if version is not None else "Versão adotada indisponível"
        self.adopted_source_label.setText(f"Currículo usado nesta candidatura: {label}")
        self.adoption_message_label.setText(message)
        self._update_adoption_buttons(source, selected_resume_version_id)

    def _update_adoption_buttons(
        self,
        source: ApplicationResumeSource | None = None,
        selected_resume_version_id: int | None = None,
    ) -> None:
        if source is None and self._adoption_state is not None:
            source = self._adoption_state.resume_source
            selected_resume_version_id = self._adoption_state.selected_resume_version_id
        can_adopt = (
            source is not None
            and self._visualized_version_id is not None
            and self._visualized_version_id != selected_resume_version_id
            and not self._adoption_running
        )
        self.adopt_button.setEnabled(can_adopt)
        self.use_original_button.setEnabled(
            source is ApplicationResumeSource.RESUME_VERSION and not self._adoption_running
        )

    def _request_adoption(self) -> None:
        version_id = self.selected_version_id
        if version_id is not None and self.adopt_button.isEnabled():
            self.adopt_version_requested.emit(version_id)

    def _request_original(self) -> None:
        if self.use_original_button.isEnabled():
            self.use_original_requested.emit()

    def _request_evaluation(self) -> None:
        version_id = self.selected_version_id
        if version_id is not None and not self._evaluation_running:
            self.evaluation_requested.emit(version_id)

    def _update_evaluation_button(self) -> None:
        self.evaluate_button.setEnabled(
            self._evaluation_available
            and self.selected_version_id is not None
            and not self._evaluation_running
        )

    @staticmethod
    def _create_read_only_content(title: str, layout: QHBoxLayout) -> QTextEdit:
        column = QVBoxLayout()
        column.addWidget(QLabel(title))
        content = QTextEdit()
        content.setReadOnly(True)
        content.setMinimumHeight(140)
        column.addWidget(content)
        layout.addLayout(column)
        return content
