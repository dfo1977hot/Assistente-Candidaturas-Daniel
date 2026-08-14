from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTextEdit,
)
import pytest

from acd.presentation.pages.workflow_page import WorkflowPage


class _TemplateService:
    def __init__(self) -> None:
        self.template = {
            "name": "Template H2A1",
            "description": "Template comportamental",
            "trigger": "Execução manual",
            "steps": [
                {
                    "name": "Verificar disponibilidade",
                    "command": "verify_job",
                },
                {
                    "name": "Aguardar ação",
                    "command": "manual_submit_application",
                    "manual": True,
                },
            ],
        }

    def get_templates(self) -> list[dict[str, object]]:
        return [dict(self.template)]

    def get_template(self, name: str) -> dict[str, object] | None:
        if name == self.template["name"]:
            return dict(self.template)
        return None


class _WorkflowService:
    def __init__(self) -> None:
        self.workflow = SimpleNamespace(
            id=7,
            name="Workflow H2A1",
            description="Descrição",
            definition="{}",
            active=True,
            version="1",
        )
        self.latest = SimpleNamespace(
            status="Concluída",
            finished_at="2026-08-13 18:00",
            started_at=None,
            created_at="2026-08-13 17:00",
        )

        self.saved: list[dict[str, object]] = []
        self.deleted: list[int] = []
        self.executed: list[tuple[int, dict[str, int]]] = []
        self.list_workflows_calls = 0

    def list_workflows(self):
        self.list_workflows_calls += 1
        return [self.workflow]

    def parse_definition(self, workflow):
        del workflow
        return {
            "trigger": "Execução manual",
            "steps": [
                {
                    "name": "Verificar disponibilidade",
                    "command": "verify_job",
                }
            ],
            "schedule": None,
            "target_status": "",
        }

    def latest_execution(self, workflow_id: int):
        assert workflow_id == 7
        return self.latest

    def get_workflow(self, workflow_id: int):
        if workflow_id == 7:
            return self.workflow
        return None

    def save_workflow(self, workflow_id, **kwargs):
        self.saved.append(
            {
                "workflow_id": workflow_id,
                **kwargs,
            }
        )
        return self.workflow

    def duplicate_workflow(self, workflow_id: int):
        assert workflow_id == 7
        return SimpleNamespace(id=8)

    def delete_workflow(self, workflow_id: int) -> bool:
        self.deleted.append(workflow_id)
        return True

    def execute_assisted(
        self,
        workflow_id: int,
        *,
        context,
        progress,
        cancel_requested,
    ):
        self.executed.append((workflow_id, dict(context)))
        assert not cancel_requested()

        progress(
            50,
            "Verificar disponibilidade",
            "Em execução",
        )
        progress(
            100,
            "Verificar disponibilidade",
            "Concluída",
        )

        return {
            "status": "Concluída",
            "execution_id": 123,
        }


class _JobService:
    def list_jobs(self):
        return [
            SimpleNamespace(
                id=10,
                title="Engenheiro de Produção",
            ),
            SimpleNamespace(
                id=20,
                title="Coordenador de Logística",
            ),
        ]


class _ApplicationService:
    def list_applications(self):
        return [
            SimpleNamespace(
                id=100,
                job_id=10,
                status="Enviada",
            ),
            SimpleNamespace(
                id=101,
                job_id=20,
                status="Entrevista",
            ),
            SimpleNamespace(
                id=102,
                job_id=10,
                status="Em análise",
            ),
        ]


class _CurriculumService:
    def list_curricula(self):
        return [
            SimpleNamespace(
                id=200,
                name="Currículo Principal",
                version="1",
            ),
            SimpleNamespace(
                id=201,
                name="Currículo Logística",
                version="2",
            ),
        ]


class _SchedulerService:
    def __init__(self, due: bool = True) -> None:
        self.due = due
        self.due_calls = 0
        self.run_calls = 0

    def due_schedules(self):
        self.due_calls += 1
        return [SimpleNamespace(id=1)] if self.due else []

    def run_due(self):
        self.run_calls += 1
        return {"executed": 1}


class _SchedulerExecutor:
    def __init__(self, running: bool = False) -> None:
        self.is_running = running
        self.tasks = []

    def execute(self, task) -> None:
        self.tasks.append(task)
        task()


def _page(
    *,
    scheduler_service=None,
) -> tuple[WorkflowPage, _WorkflowService]:
    workflow_service = _WorkflowService()

    page = WorkflowPage(
        template_service=_TemplateService(),  # type: ignore[arg-type]
        workflow_service=workflow_service,  # type: ignore[arg-type]
        job_service=_JobService(),  # type: ignore[arg-type]
        application_service=_ApplicationService(),  # type: ignore[arg-type]
        curriculum_service=_CurriculumService(),  # type: ignore[arg-type]
        scheduler_service=scheduler_service,  # type: ignore[arg-type]
    )

    return page, workflow_service


def test_workflow_page_loads_table_and_filters_by_name(qapp) -> None:
    page, service = _page()

    assert page.table.rowCount() == 1
    assert page.table.item(0, 0).text() == "7"
    assert page.table.item(0, 1).text() == "Workflow H2A1"
    assert page.table.item(0, 2).text() == "Execução manual"
    assert page.table.item(0, 3).text() == "1"
    assert page.table.item(0, 4).text() == "Ativo"
    assert page.table.item(0, 6).text() == "Concluída"

    page.search_input.setText("inexistente")
    qapp.processEvents()

    assert page.table.rowCount() == 0

    page.search_input.setText("workflow")
    qapp.processEvents()

    assert page.table.rowCount() == 1
    assert service.list_workflows_calls >= 3


def test_workflow_page_loads_selected_workflow_and_roundtrips_steps(
    qapp,
) -> None:
    page, _service = _page()

    page.table.selectRow(0)
    qapp.processEvents()

    assert page.current_workflow_id == 7
    assert page.name_input.text() == "Workflow H2A1"
    assert page.description_input.toPlainText() == "Descrição"
    assert page.active_check.isChecked()
    assert page.trigger_combo.currentText() == "Execução manual"
    assert page.steps_list.count() == 1

    steps = page._steps()

    assert steps == [
        {
            "name": "Verificar disponibilidade",
            "command": "verify_job",
        }
    ]

    page.table.clearSelection()
    page._load_selected_workflow()

    page.current_workflow_id = None
    page.table.setRowCount(1)
    page.table.setItem(0, 0, None)
    page.table.selectRow(0)
    page._load_selected_workflow()

    assert page.current_workflow_id is None


def test_workflow_page_template_add_move_remove_and_conditions(
    qapp,
) -> None:
    page, _service = _page()

    page.template_combo.setCurrentText("Template H2A1")
    page._use_template()

    assert page.current_workflow_id is None
    assert page.name_input.text() == "Template H2A1"
    assert page.description_input.toPlainText() == "Template comportamental"
    assert page.steps_list.count() == 2

    page.step_combo.setCurrentIndex(0)
    page._add_step()

    assert page.steps_list.count() == 3

    manual_index = page.step_combo.findData(
        "manual_submit_application"
    )
    assert manual_index >= 0

    page.step_combo.setCurrentIndex(manual_index)
    page._add_step()

    manual_item = page.steps_list.item(
        page.steps_list.count() - 1
    )
    manual_data = manual_item.data(
        Qt.ItemDataRole.UserRole
    )

    assert manual_data["manual"] is True

    page.steps_list.setCurrentRow(0)
    page._move_step(-1)

    assert page.steps_list.currentRow() == 0

    page._move_step(1)

    assert page.steps_list.currentRow() == 1

    page.condition_field_combo.setCurrentIndex(1)
    selected_field = page.condition_field_combo.currentData()
    assert selected_field

    page.condition_operator_combo.setCurrentText("==")
    page.condition_value_input.setText("75")
    page.condition_false_combo.setCurrentText(
        "Encerrar workflow"
    )
    page._apply_step_condition()

    current = page.steps_list.currentItem()
    assert current is not None

    data = current.data(Qt.ItemDataRole.UserRole)
    condition = data["condition"]

    assert condition["field"] == selected_field
    assert condition["operator"] == "=="
    assert condition["value"] == "75"
    assert condition["on_false"] == "Encerrar workflow"

    page._load_step_condition(current)

    assert (
        page.condition_field_combo.currentData()
        == selected_field
    )
    assert page.condition_value_input.text() == "75"

    page.condition_field_combo.setCurrentIndex(0)
    page._apply_step_condition()

    data = current.data(Qt.ItemDataRole.UserRole)
    assert "condition" not in data

    before = page.steps_list.count()
    page._remove_step()

    assert page.steps_list.count() == before - 1

    page.steps_list.setCurrentRow(-1)
    page._remove_step()

    assert page.steps_list.count() == before - 1


def test_workflow_page_loads_and_filters_execution_context(
    qapp,
) -> None:
    page, _service = _page()

    assert page.job_combo.count() == 3
    assert page.curriculum_combo.count() == 3
    assert page.application_combo.count() == 1

    job_index = page.job_combo.findData(10)
    assert job_index >= 0

    page.job_combo.setCurrentIndex(job_index)
    qapp.processEvents()

    application_ids = {
        page.application_combo.itemData(index)
        for index in range(page.application_combo.count())
    }

    assert application_ids == {None, 100, 102}
    assert 101 not in application_ids

    application_index = page.application_combo.findData(102)
    curriculum_index = page.curriculum_combo.findData(201)

    page.application_combo.setCurrentIndex(application_index)
    page.curriculum_combo.setCurrentIndex(curriculum_index)

    context = page._execution_context()

    assert context == {
        "job_id": 10,
        "application_id": 102,
        "curriculum_id": 201,
    }

    page.job_combo.setCurrentIndex(0)
    qapp.processEvents()

    assert page.application_combo.count() == 1


def test_workflow_page_schedule_definition_and_controls(qapp) -> None:
    page, _service = _page()

    assert page._schedule_definition() is None

    page.trigger_combo.setCurrentText("Agendado")

    with pytest.raises(
        ValueError,
        match="Informe data e hora",
    ):
        page._schedule_definition()

    page.schedule_at_input.setText("2026-08-14 09:30")

    schedule = page._schedule_definition()

    assert schedule is not None
    assert schedule["scheduled_at"] == "2026-08-14T09:30"
    assert schedule["active"] is True
    assert schedule["last_run_at"] is None
    assert schedule["next_run_at"] == "2026-08-14T09:30"

    page._set_execution_controls(True)

    assert not page.save_btn.isEnabled()
    assert not page.execute_btn.isEnabled()
    assert not page.job_combo.isEnabled()
    assert page.cancel_btn.isEnabled()

    page._set_execution_controls(False)

    assert page.save_btn.isEnabled()
    assert page.execute_btn.isEnabled()
    assert page.job_combo.isEnabled()
    assert not page.cancel_btn.isEnabled()


def test_workflow_page_save_duplicate_delete_and_clear(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    warnings: list[str] = []
    infos: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )

    page.name_input.clear()
    page._save()

    assert warnings == ["Informe o nome do workflow."]
    assert service.saved == []

    page.name_input.setText("Workflow salvo")
    page.description_input.setPlainText("Descrição salva")
    page.current_workflow_id = None

    page._save()

    assert len(service.saved) == 1
    assert service.saved[0]["workflow_id"] is None
    assert service.saved[0]["name"] == "Workflow salvo"
    assert page.current_workflow_id == 7
    assert infos == ["O registro foi salvo"]

    page._duplicate()

    assert page.table.rowCount() == 1

    page.current_workflow_id = 7
    page._delete()

    assert service.deleted == [7]
    assert page.current_workflow_id is None
    assert page.name_input.text() == ""
    assert page.description_input.toPlainText() == ""
    assert page.progress_bar.value() == 0
    assert page.progress_label.text() == "Pronto"


def test_workflow_page_executes_and_updates_progress(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page.current_workflow_id = None
    page._execute()

    assert messages == ["Selecione um workflow."]

    page.current_workflow_id = 7

    job_index = page.job_combo.findData(10)
    curriculum_index = page.curriculum_combo.findData(200)

    page.job_combo.setCurrentIndex(job_index)
    qapp.processEvents()
    page.curriculum_combo.setCurrentIndex(curriculum_index)

    page._execute()

    assert service.executed == [
        (
            7,
            {
                "job_id": 10,
                "curriculum_id": 200,
            },
        )
    ]
    assert page.progress_bar.value() == 100
    assert page.progress_label.text() == "Concluída"
    assert page.execute_btn.isEnabled()
    assert not page.cancel_btn.isEnabled()

    page._cancel()

    assert page._cancel_requested is True
    assert (
        page.progress_label.text()
        == "Cancelamento solicitado..."
    )


def test_workflow_page_scheduler_runs_only_when_due(qapp) -> None:
    scheduler = _SchedulerService(due=True)
    page, _service = _page(scheduler_service=scheduler)

    executor = _SchedulerExecutor()
    page._scheduler_executor = executor  # type: ignore[assignment]

    page._run_due_schedules()

    assert scheduler.due_calls == 1
    assert scheduler.run_calls == 1
    assert len(executor.tasks) == 1

    scheduler.due = False
    page._run_due_schedules()

    assert scheduler.due_calls == 2
    assert scheduler.run_calls == 1

    executor.is_running = True
    page._run_due_schedules()

    assert scheduler.due_calls == 2

    page._scheduler_started = False
    page.start_scheduler()

    assert page._scheduler_started is True
    assert page._scheduler_timer.isActive()

    page.start_scheduler()

    assert page._scheduler_started is True

    page._scheduler_timer.stop()


def test_workflow_page_on_enter_refreshes_context_workflows_and_scheduler(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    calls: list[str] = []

    monkeypatch.setattr(
        page,
        "_load_execution_context",
        lambda: calls.append("context"),
    )
    monkeypatch.setattr(
        page,
        "_load_workflows",
        lambda: calls.append("workflows"),
    )
    monkeypatch.setattr(
        page,
        "start_scheduler",
        lambda: calls.append("scheduler"),
    )

    previous_calls = service.list_workflows_calls

    page.on_enter()

    assert calls == [
        "context",
        "workflows",
        "scheduler",
    ]
    assert service.list_workflows_calls == previous_calls


def test_workflow_page_history_loads_logs_and_executes_recovery_actions(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()
    page.current_workflow_id = 7

    execution = SimpleNamespace(
        id=501,
        status="Falhou",
        current_step=2,
        started_at="2026-08-13 18:00",
        finished_at="2026-08-13 18:05",
        result="Falha simulada",
    )
    log = SimpleNamespace(
        created_at="2026-08-13 18:04",
        level="error",
        message="Erro controlado",
    )

    calls: list[tuple[str, object]] = []

    service.list_executions = (  # type: ignore[attr-defined]
        lambda workflow_id, limit=100: [execution]
    )
    service.list_logs = (  # type: ignore[attr-defined]
        lambda execution_id: [log]
    )

    def retry_failed_step(execution_id: int):
        calls.append(("retry", execution_id))
        return {
            "status": "Concluída",
            "message": "Etapa reexecutada",
        }

    def resume_execution(
        execution_id: int,
        *,
        from_failed_step: bool = False,
    ):
        calls.append(
            (
                "resume_failed"
                if from_failed_step
                else "resume",
                execution_id,
            )
        )
        return {
            "status": "Concluída",
        }

    service.retry_failed_step = retry_failed_step  # type: ignore[attr-defined]
    service.resume_execution = resume_execution  # type: ignore[attr-defined]

    messages: list[tuple[str, str]] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, title, message: messages.append(
            (
                str(title),
                str(message),
            )
        ),
    )

    def fake_exec(dialog: QDialog) -> int:
        table = dialog.findChild(QTableWidget)
        details = dialog.findChild(QTextEdit)

        assert table is not None
        assert details is not None
        assert table.rowCount() == 1

        assert table.item(0, 0).text() == "501"
        assert table.item(0, 1).text() == "Falhou"
        assert table.item(0, 2).text() == "2"
        assert table.item(0, 5).text() == "Falha simulada"

        table.selectRow(0)
        qapp.processEvents()

        assert "Erro controlado" in details.toPlainText()
        assert "[error]" in details.toPlainText()

        buttons = {
            button.text(): button
            for button in dialog.findChildren(QPushButton)
        }

        buttons["Reexecutar etapa que falhou"].click()
        buttons["Retomar workflow"].click()
        buttons["Retomar a partir da falha"].click()

        qapp.processEvents()

        return 0

    monkeypatch.setattr(
        QDialog,
        "exec",
        fake_exec,
    )

    page._show_history()

    assert calls == [
        ("retry", 501),
        ("resume", 501),
        ("resume_failed", 501),
    ]
    assert (
        "Reexecutar etapa",
        "Etapa reexecutada",
    ) in messages
    assert (
        "Retomar workflow",
        "Concluída",
    ) in messages