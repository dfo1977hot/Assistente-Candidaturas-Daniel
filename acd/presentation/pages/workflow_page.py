from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QComboBox,
)

from acd.presentation.pages.base_page import BasePage
from acd.services.workflow_template_service import WorkflowTemplateService
from acd.services.workflow_service import WorkflowService


class WorkflowPage(BasePage):
    """Page for workflow designer and execution."""

    def __init__(self) -> None:
        super().__init__("Workflow Designer")
        self.template_service = WorkflowTemplateService()
        self.workflow_service = WorkflowService()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the workflow page UI."""
        # Templates section
        templates_label = QLabel("Templates Disponíveis")
        templates_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        self.layout.addWidget(templates_label)

        self.templates_list = QListWidget()
        templates = self.template_service.get_templates()
        for template in templates:
            item = QListWidgetItem(template["name"])
            item.setData(32, template)
            self.templates_list.addItem(item)

        self.layout.addWidget(self.templates_list)

        # Buttons section
        buttons_layout = QHBoxLayout()
        self.execute_btn = QPushButton("Executar Fluxo")
        self.execute_btn.clicked.connect(self._on_execute_workflow)
        buttons_layout.addWidget(self.execute_btn)

        self.layout.addLayout(buttons_layout)

    def _on_execute_workflow(self) -> None:
        """Handle workflow execution."""
        current_item = self.templates_list.currentItem()
        if current_item is None:
            return
        template = current_item.data(32)
        result = self.template_service.create_workflow_from_template(template["name"])
