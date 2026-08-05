from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.pages.application_wizard.company_step import (
    CompanyStep,
)
from acd.presentation.pages.application_wizard.description_step import (
    DescriptionStep,
)
from acd.presentation.pages.application_wizard.job_step import (
    JobStep,
)
from acd.presentation.pages.application_wizard.review_step import (
    ReviewStep,
)
from acd.presentation.pages.application_wizard.wizard_navigator import (
    WizardNavigator,
)
from acd.presentation.pages.new_application_view_model import (
    NewApplicationViewModel,
)


class ApplicationWizard(QWidget):
    """
    Wizard responsável pelo fluxo inteligente de candidatura.
    """

    def __init__(
        self,
        view_model: NewApplicationViewModel | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._view_model = (
            view_model
            if view_model is not None
            else NewApplicationViewModel()
        )

        self._navigator = WizardNavigator()

        self.stack = QStackedWidget()

        self.company_step = CompanyStep()

        self._register_step(self.company_step)

        self.company_step.completed.connect(
            self._company_completed
        )

        self._build_ui()

    @property
    def navigator(self) -> WizardNavigator:
        return self._navigator

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel(
                "Assistente Inteligente de Candidaturas"
            )
        )

        layout.addWidget(self.stack)

    def _register_step(
        self,
        step: QWidget,
    ) -> None:
        self.stack.addWidget(step)
        self._navigator.configure(
            self.stack.count()
        )

    def _register_job_step(self) -> None:
        if hasattr(self, "_job_step"):
            return

        self._job_step = JobStep()

        self._register_step(self._job_step)

        self._job_step.completed.connect(
            self._job_completed
        )

    def _register_description_step(self) -> None:
        if hasattr(self, "_description_step"):
            return

        self._description_step = DescriptionStep()

        self._register_step(self._description_step)

        self._description_step.completed.connect(
            self._description_completed
        )

    def _register_review_step(self) -> None:
        if hasattr(self, "_review_step"):
            return

        self._review_step = ReviewStep(
            self._view_model
        )

        self._register_step(
            self._review_step
        )

        self._review_step.completed.connect(
            self._review_completed
        )

    def _go_next(self) -> None:
        index = self._navigator.next()

        self.stack.setCurrentIndex(index)

        widget = self.stack.currentWidget()

        if hasattr(widget, "on_enter"):
            widget.on_enter()

    def _go_previous(self) -> None:
        index = self._navigator.previous()

        self.stack.setCurrentIndex(index)

    def _company_completed(
        self,
        company_name: str,
    ) -> None:
        self._view_model.set_company_name(
            company_name
        )

        self._register_job_step()

        self._go_next()

    def _job_completed(
        self,
        job_title: str,
        job_url: str,
    ) -> None:
        self._view_model.set_job_title(
            job_title
        )

        self._view_model.set_job_url(
            job_url
        )

        self._register_description_step()

        self._go_next()

    def _description_completed(
        self,
        description: str,
    ) -> None:
        self._view_model.set_job_description(
            description
        )

        self._register_review_step()

        self._go_next()

    def _review_completed(self) -> None:
        self._view_model.start_application()