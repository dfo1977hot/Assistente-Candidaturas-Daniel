from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from acd.presentation.pages.base_page import BasePage
from acd.services.application_service import ApplicationService
from acd.services.curriculum_service import CurriculumService
from acd.services.job_service import JobService
from acd.services.workflow_service import WorkflowService
from acd.services.workflow_template_service import WorkflowTemplateService


class WorkflowPage(BasePage):
    """Workflow designer, manual executor and execution history."""

    STEP_CATALOG = (
        ("Verificar disponibilidade da vaga", "verify_job"),
        ("Detectar URL da candidatura", "detect_application_url"),
        ("Buscar dados da empresa", "enrich_company"),
        ("Pesquisar remuneração", "research_salary"),
        ("Analisar aderência", "analyze_fit"),
        ("Selecionar currículo", "select_resume"),
        ("Gerar currículo otimizado", "generate_resume"),
        ("Gerar carta", "generate_cover_letter"),
        ("Criar/atualizar candidatura", "register_application"),
        ("Revisar candidatura", "review_application"),
        ("Verificar prazo de follow-up", "check_follow_up"),
        ("Classificar vaga encerrada", "classify_closed_job"),
        ("Aguardar conclusão manual", "manual_submit_application"),
    )

    def __init__(
        self,
        template_service: WorkflowTemplateService,
        workflow_service: WorkflowService,
        job_service: JobService | None = None,
        application_service: ApplicationService | None = None,
        curriculum_service: CurriculumService | None = None,
    ) -> None:
        super().__init__("Workflows")
        self.template_service = template_service
        self.workflow_service = workflow_service
        self.job_service = job_service
        self.application_service = application_service
        self.curriculum_service = curriculum_service
        self.current_workflow_id: int | None = None
        self._cancel_requested = False
        self._setup_ui()
        self._load_execution_context()
        self._load_workflows()

    def _setup_ui(self) -> None:
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar workflows")
        self.search_input.textChanged.connect(self._load_workflows)
        search_row.addWidget(QLabel("Pesquisar"))
        search_row.addWidget(self.search_input, 1)
        self.layout.addLayout(search_row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Workflow",
                "Gatilho",
                "Etapas",
                "Status",
                "Última execução",
                "Resultado",
            ]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._load_selected_workflow)
        self.layout.addWidget(self.table)

        editor = QWidget()
        editor_layout = QHBoxLayout(editor)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        left = QFormLayout()
        self.name_input = QLineEdit()
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(
            [
                "Execução manual",
                "Vaga importada",
                "Vaga criada manualmente",
                "Candidatura criada",
                "Mudança de status",
            ]
        )
        self.active_check = QCheckBox("Ativo")
        self.active_check.setChecked(True)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(90)
        left.addRow("Nome", self.name_input)
        left.addRow("Gatilho", self.trigger_combo)
        left.addRow("", self.active_check)
        left.addRow("Descrição", self.description_input)

        template_row = QHBoxLayout()
        self.template_combo = QComboBox()
        for template in self.template_service.get_templates():
            self.template_combo.addItem(template["name"])
        self.use_template_btn = QPushButton("Usar template")
        self.use_template_btn.clicked.connect(self._use_template)
        template_row.addWidget(self.template_combo, 1)
        template_row.addWidget(self.use_template_btn)
        left.addRow("Template", template_row)

        editor_layout.addLayout(left, 1)

        right = QVBoxLayout()
        right.addWidget(QLabel("Etapas"))
        self.steps_list = QListWidget()
        self.steps_list.setAlternatingRowColors(True)
        right.addWidget(self.steps_list)

        step_row = QHBoxLayout()
        self.step_combo = QComboBox()
        for name, command in self.STEP_CATALOG:
            self.step_combo.addItem(name, command)
        self.add_step_btn = QPushButton("+ Adicionar")
        self.add_step_btn.clicked.connect(self._add_step)
        step_row.addWidget(self.step_combo, 1)
        step_row.addWidget(self.add_step_btn)
        right.addLayout(step_row)

        order_row = QHBoxLayout()
        self.up_btn = QPushButton("↑")
        self.down_btn = QPushButton("↓")
        self.remove_step_btn = QPushButton("Remover")
        self.up_btn.clicked.connect(lambda: self._move_step(-1))
        self.down_btn.clicked.connect(lambda: self._move_step(1))
        self.remove_step_btn.clicked.connect(self._remove_step)
        order_row.addWidget(self.up_btn)
        order_row.addWidget(self.down_btn)
        order_row.addWidget(self.remove_step_btn)
        order_row.addStretch(1)
        right.addLayout(order_row)
        editor_layout.addLayout(right, 1)

        self.layout.addWidget(editor)

        context_row = QFormLayout()
        self.job_combo = QComboBox()
        self.application_combo = QComboBox()
        self.curriculum_combo = QComboBox()
        self.job_combo.currentIndexChanged.connect(self._filter_applications)
        context_row.addRow("Vaga alvo", self.job_combo)
        context_row.addRow("Candidatura alvo", self.application_combo)
        context_row.addRow("Currículo alvo", self.curriculum_combo)
        self.layout.addLayout(context_row)

        progress_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label = QLabel("Pronto")
        progress_row.addWidget(self.progress_bar, 1)
        progress_row.addWidget(self.progress_label)
        self.layout.addLayout(progress_row)

        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Salvar")
        self.duplicate_btn = QPushButton("Duplicar")
        self.delete_btn = QPushButton("Excluir")
        self.execute_btn = QPushButton("Executar agora")
        self.cancel_btn = QPushButton("Cancelar")
        self.history_btn = QPushButton("Histórico")
        self.save_btn.clicked.connect(self._save)
        self.duplicate_btn.clicked.connect(self._duplicate)
        self.delete_btn.clicked.connect(self._delete)
        self.execute_btn.clicked.connect(self._execute)
        self.cancel_btn.clicked.connect(self._cancel)
        self.history_btn.clicked.connect(self._show_history)
        for button in (
            self.save_btn,
            self.duplicate_btn,
            self.delete_btn,
            self.execute_btn,
            self.cancel_btn,
            self.history_btn,
        ):
            buttons.addWidget(button)
        buttons.addStretch(1)
        self.layout.addLayout(buttons)
        self.cancel_btn.setEnabled(False)

    def _load_workflows(self) -> None:
        query = self.search_input.text().strip().casefold()
        workflows = self.workflow_service.list_workflows()
        rows = []
        for workflow in workflows:
            if query and query not in workflow.name.casefold():
                continue
            definition = self.workflow_service.parse_definition(workflow)
            latest = self.workflow_service.latest_execution(workflow.id)
            rows.append((workflow, definition, latest))

        self.table.setRowCount(len(rows))
        for row, (workflow, definition, latest) in enumerate(rows):
            values = [
                str(workflow.id),
                workflow.name,
                definition["trigger"],
                str(len(definition["steps"])),
                "Ativo" if workflow.active else "Inativo",
                (
                    str(latest.finished_at or latest.started_at or latest.created_at)
                    if latest is not None
                    else ""
                ),
                latest.status if latest is not None else "",
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

    def _load_selected_workflow(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        item = self.table.item(rows[0].row(), 0)
        if item is None:
            return
        workflow = self.workflow_service.get_workflow(int(item.text()))
        if workflow is None:
            return
        self.current_workflow_id = workflow.id
        definition = self.workflow_service.parse_definition(workflow)
        self.name_input.setText(workflow.name)
        self.description_input.setPlainText(workflow.description)
        self.active_check.setChecked(workflow.active)
        self.trigger_combo.setCurrentText(definition["trigger"])
        self._set_steps(definition["steps"])

    def _set_steps(self, steps: list[dict[str, Any]]) -> None:
        self.steps_list.clear()
        for step in steps:
            item = QListWidgetItem(str(step.get("name") or "Etapa"))
            item.setData(Qt.ItemDataRole.UserRole, dict(step))
            self.steps_list.addItem(item)

    def _steps(self) -> list[dict[str, Any]]:
        result = []
        for index in range(self.steps_list.count()):
            item = self.steps_list.item(index)
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            result.append(dict(data))
        return result

    def _use_template(self) -> None:
        template = self.template_service.get_template(
            self.template_combo.currentText()
        )
        if template is None:
            return
        self.current_workflow_id = None
        self.name_input.setText(template["name"])
        self.description_input.setPlainText(template["description"])
        self.trigger_combo.setCurrentText(
            template.get("trigger", "Execução manual")
        )
        self.active_check.setChecked(True)
        self._set_steps(template["steps"])

    def _add_step(self) -> None:
        name = self.step_combo.currentText()
        command = str(self.step_combo.currentData() or "")
        step = {"name": name, "command": command}
        if command.startswith("manual_"):
            step["manual"] = True
        item = QListWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, step)
        self.steps_list.addItem(item)

    def _move_step(self, direction: int) -> None:
        row = self.steps_list.currentRow()
        target = row + direction
        if row < 0 or target < 0 or target >= self.steps_list.count():
            return
        item = self.steps_list.takeItem(row)
        self.steps_list.insertItem(target, item)
        self.steps_list.setCurrentRow(target)

    def _remove_step(self) -> None:
        row = self.steps_list.currentRow()
        if row >= 0:
            self.steps_list.takeItem(row)

    def _save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Workflows", "Informe o nome do workflow.")
            return
        workflow = self.workflow_service.save_workflow(
            self.current_workflow_id,
            name=name,
            description=self.description_input.toPlainText().strip(),
            trigger=self.trigger_combo.currentText(),
            steps=self._steps(),
            active=self.active_check.isChecked(),
        )
        self.current_workflow_id = workflow.id
        self._load_workflows()
        self._select_workflow_row(workflow.id)
        QMessageBox.information(self, "Workflows", "O registro foi salvo")

    def _duplicate(self) -> None:
        if self.current_workflow_id is None:
            return
        workflow = self.workflow_service.duplicate_workflow(
            self.current_workflow_id
        )
        self._load_workflows()
        self._select_workflow_row(workflow.id)

    def _delete(self) -> None:
        if self.current_workflow_id is None:
            return
        answer = QMessageBox.question(
            self,
            "Excluir workflow",
            "Deseja excluir este workflow e seu histórico de execuções?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.workflow_service.delete_workflow(self.current_workflow_id)
        self.current_workflow_id = None
        self._clear_form()
        self._load_workflows()

    def _execute(self) -> None:
        if self.current_workflow_id is None:
            QMessageBox.warning(self, "Workflows", "Selecione um workflow.")
            return
        self._cancel_requested = False
        self.progress_bar.setValue(0)
        self.progress_label.setText("Iniciando...")
        self._set_execution_controls(True)
        try:
            result = self.workflow_service.execute_assisted(
                self.current_workflow_id,
                context=self._execution_context(),
                progress=self._on_progress,
                cancel_requested=lambda: self._cancel_requested,
            )
        except Exception as error:
            QMessageBox.critical(self, "Workflows", str(error))
            return
        finally:
            self._set_execution_controls(False)
        self._load_workflows()
        self._select_workflow_row(self.current_workflow_id)
        self.progress_label.setText(str(result.get("status") or "Concluída"))
        if result.get("status") == "Aguardando usuário":
            QMessageBox.information(
                self,
                "Workflow",
                "O workflow chegou a uma etapa que requer sua ação.",
            )

    def _on_progress(self, value: int, step: str, status: str) -> None:
        self.progress_bar.setValue(value)
        self.progress_label.setText(f"{value}% — {step} — {status}")
        QApplication.processEvents()

    def _cancel(self) -> None:
        self._cancel_requested = True
        self.progress_label.setText("Cancelamento solicitado...")

    def _show_history(self) -> None:
        if self.current_workflow_id is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Histórico do workflow")
        dialog.resize(900, 520)
        layout = QVBoxLayout(dialog)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(
            ["ID", "Status", "Etapa", "Início", "Fim", "Resultado"]
        )
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch
        )

        executions = self.workflow_service.list_executions(
            self.current_workflow_id,
            limit=100,
        )
        table.setRowCount(len(executions))
        for row, execution in enumerate(executions):
            values = [
                str(execution.id),
                execution.status,
                str(execution.current_step),
                str(execution.started_at or ""),
                str(execution.finished_at or ""),
                execution.result,
            ]
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))
        layout.addWidget(table)

        details = QTextEdit()
        details.setReadOnly(True)
        details.setMaximumHeight(150)
        layout.addWidget(details)

        def load_logs() -> None:
            rows = table.selectionModel().selectedRows()
            if not rows:
                details.clear()
                return
            execution_id = int(table.item(rows[0].row(), 0).text())
            logs = self.workflow_service.list_logs(execution_id)
            details.setPlainText(
                "\n".join(
                    f"{log.created_at} [{log.level}] {log.message}"
                    for log in logs
                )
            )

        table.itemSelectionChanged.connect(load_logs)

        actions = QHBoxLayout()
        retry = QPushButton("Reexecutar etapa que falhou")
        actions.addWidget(retry)
        actions.addStretch(1)
        layout.addLayout(actions)

        def retry_failed() -> None:
            rows = table.selectionModel().selectedRows()
            if not rows:
                return
            execution_id = int(table.item(rows[0].row(), 0).text())
            try:
                result = self.workflow_service.retry_failed_step(execution_id)
            except Exception as error:
                QMessageBox.warning(dialog, "Reexecutar etapa", str(error))
                return
            QMessageBox.information(
                dialog,
                "Reexecutar etapa",
                str(result.get("message") or result.get("status") or "Concluída"),
            )
            load_logs()

        retry.clicked.connect(retry_failed)

        close_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_buttons.rejected.connect(dialog.reject)
        layout.addWidget(close_buttons)
        dialog.exec()
        self._select_workflow_row(self.current_workflow_id)

    def _load_execution_context(self) -> None:
        self.job_combo.clear()
        self.job_combo.addItem("Selecione uma vaga", None)
        if self.job_service is not None:
            for job in self.job_service.list_jobs():
                self.job_combo.addItem(f"{job.title} (#{job.id})", job.id)

        self.curriculum_combo.clear()
        self.curriculum_combo.addItem("Seleção automática", None)
        if self.curriculum_service is not None:
            for curriculum in self.curriculum_service.list_curricula():
                self.curriculum_combo.addItem(
                    f"{curriculum.name} — {curriculum.version}", curriculum.id
                )
        self._filter_applications()

    def _filter_applications(self) -> None:
        selected = self.application_combo.currentData()
        job_id = self.job_combo.currentData()
        self.application_combo.clear()
        self.application_combo.addItem("Nenhuma / localizar automaticamente", None)
        if self.application_service is not None and job_id is not None:
            for application in self.application_service.list_applications():
                if application.job_id == int(job_id):
                    self.application_combo.addItem(
                        f"Candidatura #{application.id} — {application.status}",
                        application.id,
                    )
        index = self.application_combo.findData(selected)
        if index >= 0:
            self.application_combo.setCurrentIndex(index)

    def _execution_context(self) -> dict[str, int]:
        context = {}
        for key, combo in (
            ("job_id", self.job_combo),
            ("application_id", self.application_combo),
            ("curriculum_id", self.curriculum_combo),
        ):
            if combo.currentData() is not None:
                context[key] = int(combo.currentData())
        return context

    def _set_execution_controls(self, running: bool) -> None:
        for control in (
            self.save_btn,
            self.duplicate_btn,
            self.delete_btn,
            self.execute_btn,
            self.history_btn,
            self.job_combo,
            self.application_combo,
            self.curriculum_combo,
        ):
            control.setEnabled(not running)
        self.cancel_btn.setEnabled(running)

    def _select_workflow_row(self, workflow_id: int | None) -> None:
        if workflow_id is None:
            return
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None and item.text() == str(workflow_id):
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                return

    def _clear_form(self) -> None:
        self.name_input.clear()
        self.description_input.clear()
        self.trigger_combo.setCurrentText("Execução manual")
        self.active_check.setChecked(True)
        self.steps_list.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Pronto")
