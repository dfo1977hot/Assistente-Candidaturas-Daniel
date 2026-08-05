from __future__ import annotations

from enum import Enum, auto

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.models.application_wizard_state import (
    ApplicationWizardState,
)


class WizardStep(Enum):
    """
    Etapas do fluxo de candidatura.
    """

    COMPANY = auto()
    JOB = auto()
    DESCRIPTION = auto()
    ANALYSIS = auto()
    RESUME = auto()
    COVER_LETTER = auto()
    CONFIRMATION = auto()


class ApplicationWizard(QWidget):
    """
    Container responsável por controlar o fluxo do Wizard.

    Não conhece regras de negócio.
    Não conhece ApplicationFacade.
    Não conhece IA.

    Sua única responsabilidade é controlar a navegação entre as etapas.
    """

    step_changed = Signal(WizardStep)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.state = ApplicationWizardState()

        self.stack = QStackedWidget()

        self.previous_button = QPushButton("Anterior")
        self.next_button = QPushButton("Próximo")
        self.finish_button = QPushButton("Concluir")

        self._current_step = WizardStep.COMPANY

        self._build_ui()

        self.previous_button.clicked.connect(self.previous_step)
        self.next_button.clicked.connect(self.next_step)

        self._update_buttons()

    @property
    def current_step(self) -> WizardStep:
        page = self.current_page

        assert page is not None

        wizard_page = page.widget

        wizard_page.on_leave()

        if not wizard_page.validate_page():
            return
        # return self._current_step

    def add_step(self, widget: QWidget) -> None:
        self.stack.addWidget(widget)

    def next_step(self) -> None:
        index = self.stack.currentIndex()

        page = self.current_page

        assert page is not None

        page.widget.on_enter()

        if index >= self.stack.count() - 1:
            return

        self.stack.setCurrentIndex(index + 1)

        self._current_step = list(WizardStep)[index + 1]

        self._update_buttons()

        self.step_changed.emit(self._current_step)

    def previous_step(self) -> None:

        page = self.current_page

        assert page is not None

        page.widget.on_leave()

        index = self.stack.currentIndex()

        if index <= 0:
            return

        self.stack.setCurrentIndex(index - 1)

        page = self.current_page

        assert page is not None

        page.widget.on_enter()

        self._current_step = list(WizardStep)[index - 1]

        self._update_buttons()

        self.step_changed.emit(self._current_step)

    def _update_buttons(self) -> None:
        index = self.stack.currentIndex()

        self.previous_button.setEnabled(index > 0)

        last = self.stack.count() - 1

        self.next_button.setVisible(index < last)

        self.finish_button.setVisible(index == last)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(self.stack)

        buttons = QHBoxLayout()

        buttons.addWidget(self.previous_button)

        buttons.addStretch()

        buttons.addWidget(self.next_button)

        buttons.addWidget(self.finish_button)

        layout.addLayout(buttons)