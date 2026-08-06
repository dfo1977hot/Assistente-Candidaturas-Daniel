from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.pages.base_page import BasePage


class AssistantPage(BasePage):
    """AI Agent Assistant page."""

    def __init__(
        self,
        *,
        orchestrator: object,
        repository: object,
        memory_service: object,
        execution_service: object,
    ) -> None:
        super().__init__("Assistente")
        self.orchestrator = orchestrator
        self.repository = repository
        self.memory_service = memory_service
        self.execution_service = execution_service

        self._current_plan = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the assistant UI."""
        layout = QHBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Left panel: Chat
        left_panel = self.create_chat_panel()
        layout.addWidget(left_panel, stretch=2)

        # Right panel: Plan and execution
        right_panel = self.create_plan_panel()
        layout.addWidget(right_panel, stretch=1)

        self.setLayout(layout)

    def create_chat_panel(self) -> QWidget:
        """Create chat panel."""
        widget = QFrame()
        widget.setStyleSheet(
            "QFrame { border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; }"
        )

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Assistente de IA")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Chat history (read-only)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(300)
        self.chat_display.setStyleSheet(
            "QTextEdit { border: 1px solid #ccc; border-radius: 4px; padding: 8px; }"
        )
        layout.addWidget(self.chat_display)

        # Input field
        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Digite seu objetivo ou pergunta aqui...")
        self.chat_input.setMaximumHeight(100)
        self.chat_input.setStyleSheet(
            "QTextEdit { border: 1px solid #ccc; border-radius: 4px; padding: 8px; }"
        )
        layout.addWidget(self.chat_input)

        # Send button
        send_btn = QPushButton("Enviar")
        send_btn.setStyleSheet(
            "QPushButton { background-color: #0066cc; color: white; padding: 8px; border-radius: 4px; }"
        )
        send_btn.clicked.connect(self._on_send_message)
        layout.addWidget(send_btn)

        widget.setLayout(layout)
        return widget

    def create_plan_panel(self) -> QWidget:
        """Create plan and execution panel."""
        widget = QFrame()
        widget.setStyleSheet(
            "QFrame { border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; }"
        )

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Plano de Execução")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Plan details
        self.plan_details = QTextEdit()
        self.plan_details.setReadOnly(True)
        self.plan_details.setMaximumHeight(150)
        self.plan_details.setStyleSheet(
            "QTextEdit { border: 1px solid #ccc; border-radius: 4px; padding: 8px; }"
        )
        layout.addWidget(self.plan_details)

        # Approve button
        self.approve_btn = QPushButton("Aprovar Plano")
        self.approve_btn.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; padding: 8px; border-radius: 4px; }"
        )
        self.approve_btn.clicked.connect(self._on_approve_plan)
        self.approve_btn.setEnabled(False)
        layout.addWidget(self.approve_btn)

        # Execute button
        self.execute_btn = QPushButton("Executar")
        self.execute_btn.setStyleSheet(
            "QPushButton { background-color: #0066cc; color: white; padding: 8px; border-radius: 4px; }"
        )
        self.execute_btn.clicked.connect(self._on_execute_plan)
        self.execute_btn.setEnabled(False)
        layout.addWidget(self.execute_btn)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Execution log
        log_title = QLabel("Log de Execução")
        log_title.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(log_title)

        self.execution_log = QListWidget()
        self.execution_log.setMaximumHeight(200)
        layout.addWidget(self.execution_log)

        # Status
        self.status_label = QLabel("Pronto para receber objetivos")
        self.status_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def _on_send_message(self) -> None:
        """Handle sending a message."""
        message = self.chat_input.toPlainText().strip()
        if not message:
            return

        # Display user message
        self.chat_display.append(f"<b>Você:</b> {message}")
        self.chat_input.clear()

        # Analyze request
        analysis = self.orchestrator.analyze_request(message)

        # Display analysis
        response = f"<b>Assistente:</b> Entendido! Você quer: {analysis.get('intent')}<br>"
        response += f"Confiança: {analysis.get('confidence', 0):.0%}"
        self.chat_display.append(response)

        # Create goal based on analysis
        goal_data = {
            "title": message[:100],
            "description": message,
            "objective_type": analysis.get("intent", "job_search"),
            "priority": 1,
        }

        # Create plan
        from acd.application.agent.create_plan import create_plan

        plan_result = create_plan(
            goal_data,
            repository=self.repository,
            orchestrator=self.orchestrator,
            memory_service=self.memory_service,
        )

        if plan_result.get("success"):
            self._current_plan = plan_result
            self._display_plan(plan_result)
            self.approve_btn.setEnabled(True)
            self.status_label.setText(f"Plano criado: {plan_result.get('task_count')} tarefas")
        else:
            self.chat_display.append(
                f"<b style='color: red;'>Erro:</b> {plan_result.get('errors', ['Unknown error'])[0]}"
            )

    def _display_plan(self, plan: dict) -> None:
        """Display plan details."""
        details = f"<b>Objetivo:</b> {plan.get('title')}<br>"
        details += f"<b>Estratégia:</b> {plan.get('strategy')}<br>"
        details += f"<b>Tarefas:</b> {plan.get('task_count')}<br>"
        details += f"<b>Duração estimada:</b> {plan.get('estimated_duration_hours')} horas<br>"
        details += f"<b>Requer aprovação:</b> {'Sim' if plan.get('requires_approval') else 'Não'}"

        self.plan_details.setText(details)

    def _on_approve_plan(self) -> None:
        """Approve the current plan."""
        if not self._current_plan:
            return

        from acd.application.agent.execute_plan import approve_plan

        result = approve_plan(
            self._current_plan.get("plan_id"),
            approved=True,
            repository=self.repository,
        )

        if result.get("success"):
            self.status_label.setText("Plano aprovado! Pronto para executar.")
            self.execute_btn.setEnabled(True)
            self.approve_btn.setEnabled(False)

    def _on_execute_plan(self) -> None:
        """Execute the current plan."""
        if not self._current_plan:
            return

        from acd.application.agent.execute_plan import execute_plan

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Executando plano...")

        result = execute_plan(
            self._current_plan.get("plan_id"),
            approved=True,
            repository=self.repository,
            orchestrator=self.orchestrator,
            execution_service=self.execution_service,
        )

        # Log execution
        self.execution_log.addItem(f"Plano: {self._current_plan.get('plan_id')}")
        self.execution_log.addItem(f"Tarefas concluídas: {result.get('tasks_executed', 0)}")
        self.execution_log.addItem(f"Tarefas falhadas: {result.get('tasks_failed', 0)}")

        self.progress_bar.setValue(100)
        self.status_label.setText(
            f"Execução {'bem-sucedida' if result.get('success') else 'com falhas'}"
        )
