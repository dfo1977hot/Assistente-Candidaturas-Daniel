from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import json
from typing import Any

from acd.domain.entities.workflow import Workflow
from acd.infrastructure.repositories.workflow_repository import WorkflowRepository
from acd.infrastructure.workflow.workflow_event_bus import EventBus
from acd.infrastructure.workflow.workflow_runner import WorkflowRunner

StepHandler = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any] | None]
ProgressCallback = Callable[[int, str, str], None]
CancelCallback = Callable[[], bool]


class WorkflowService:
    """Manage workflow definitions and Sprint 1 assisted executions."""

    STEP_STATUSES = (
        "Pendente",
        "Em execução",
        "Concluída",
        "Ignorada",
        "Falhou",
        "Aguardando usuário",
        "Cancelada",
    )

    def __init__(
        self,
        repository: WorkflowRepository | None = None,
        runner: WorkflowRunner | None = None,
        event_bus: EventBus | None = None,
        step_handlers: dict[str, StepHandler] | None = None,
    ) -> None:
        self.repository = repository or WorkflowRepository()
        self.event_bus = event_bus or EventBus()
        self.runner = runner or WorkflowRunner(self.repository, self.event_bus)
        self.step_handlers = dict(step_handlers or {})

    @staticmethod
    def _definition(
        steps: list[dict[str, Any]],
        *,
        trigger: str = "Execução manual",
    ) -> str:
        return json.dumps(
            {"trigger": trigger, "steps": steps},
            ensure_ascii=False,
        )

    @staticmethod
    def parse_definition(workflow: Workflow) -> dict[str, Any]:
        try:
            value = json.loads(workflow.definition or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            value = {}
        steps = value.get("steps")
        if not isinstance(steps, list):
            steps = []
        return {
            "trigger": str(value.get("trigger") or "Execução manual"),
            "steps": steps,
        }

    def create_workflow(
        self,
        name: str,
        description: str,
        steps: list[dict[str, Any]],
        *,
        version: str = "1",
        trigger: str = "Execução manual",
        active: bool = True,
    ) -> Workflow:
        workflow = self.repository.create_workflow(
            name,
            description,
            self._definition(steps, trigger=trigger),
            version=version,
        )
        if getattr(workflow, "active", True) != active:
            workflow = self.repository.update_workflow(
                workflow.id,
                name=workflow.name,
                description=workflow.description,
                definition=workflow.definition,
                active=active,
                version=workflow.version,
            )
        return workflow

    def save_workflow(
        self,
        workflow_id: int | None,
        *,
        name: str,
        description: str,
        trigger: str,
        steps: list[dict[str, Any]],
        active: bool,
        version: str = "1",
    ) -> Workflow:
        if workflow_id is None:
            return self.create_workflow(
                name,
                description,
                steps,
                version=version,
                trigger=trigger,
                active=active,
            )
        return self.repository.update_workflow(
            workflow_id,
            name=name,
            description=description,
            definition=self._definition(steps, trigger=trigger),
            active=active,
            version=version,
        )

    def duplicate_workflow(self, workflow_id: int) -> Workflow:
        source = self.get_workflow(workflow_id)
        if source is None:
            raise ValueError("Workflow não encontrado.")
        definition = self.parse_definition(source)
        return self.create_workflow(
            f"{source.name} - Cópia",
            source.description,
            definition["steps"],
            version=source.version,
            trigger=definition["trigger"],
            active=False,
        )

    def delete_workflow(self, workflow_id: int) -> bool:
        return self.repository.delete_workflow(workflow_id)

    def execute_workflow(
        self,
        workflow_id: int,
        application_id: int | None = None,
    ) -> dict[str, Any]:
        """Preserve the legacy workflow engine entrypoint."""
        execution = self.repository.create_execution(workflow_id, application_id)
        return self.runner.run(execution)

    def execute_assisted(
        self,
        workflow_id: int,
        *,
        context: dict[str, Any] | None = None,
        progress: ProgressCallback | None = None,
        cancel_requested: CancelCallback | None = None,
    ) -> dict[str, Any]:
        """Run a Sprint 1 workflow step-by-step with progress and history."""
        workflow = self.get_workflow(workflow_id)
        if workflow is None:
            raise ValueError("Workflow não encontrado.")
        if not workflow.active:
            raise ValueError("O workflow está inativo.")

        definition = self.parse_definition(workflow)
        steps = definition["steps"]
        execution = self.repository.create_execution(workflow_id)
        execution.status = "Em execução"
        execution.started_at = datetime.now(UTC).replace(tzinfo=None)
        execution.context = json.dumps(context or {}, ensure_ascii=False)
        execution = self.repository.update_execution(execution)
        self.repository.create_log(execution.id, "info", "Workflow iniciado.")

        if not steps:
            execution.status = "Concluída"
            execution.result = "Workflow sem etapas."
            execution.finished_at = datetime.now(UTC).replace(tzinfo=None)
            return self.repository.update_execution(execution).__dict__

        started = datetime.now(UTC)
        total = len(steps)

        for index, step in enumerate(steps, start=1):
            name = str(step.get("name") or f"Etapa {index}")
            command = str(step.get("command") or "")
            if cancel_requested is not None and cancel_requested():
                execution.status = "Cancelada"
                execution.current_step = index - 1
                execution.result = f"Cancelada antes de: {name}"
                self.repository.create_log(
                    execution.id,
                    "warning",
                    f"CANCELADA|{index}|{command}|{name}",
                )
                break

            execution.current_step = index
            execution = self.repository.update_execution(execution)
            if progress is not None:
                progress(int(((index - 1) / total) * 100), name, "Em execução")
            self.repository.create_log(
                execution.id,
                "info",
                f"INICIADA|{index}|{command}|{name}",
            )

            try:
                result = self._execute_step(step, context or {})
            except Exception as error:
                execution.status = "Falhou"
                execution.result = f"{name}: {error}"
                self.repository.create_log(
                    execution.id,
                    "error",
                    f"FALHOU|{index}|{command}|{name}|{error}",
                )
                if progress is not None:
                    progress(int((index / total) * 100), name, "Falhou")
                break

            status = str((result or {}).get("status") or "Concluída")
            message = str((result or {}).get("message") or "")
            normalized = status.casefold()
            if normalized in {"aguardando usuário", "awaiting_user", "awaiting user"}:
                execution.status = "Aguardando usuário"
                execution.result = message or f"Aguardando usuário em: {name}"
                self.repository.create_log(
                    execution.id,
                    "info",
                    f"AGUARDANDO|{index}|{command}|{name}|{message}",
                )
                if progress is not None:
                    progress(int((index / total) * 100), name, "Aguardando usuário")
                break
            if normalized in {"ignorada", "skipped"}:
                self.repository.create_log(
                    execution.id,
                    "info",
                    f"IGNORADA|{index}|{command}|{name}|{message}",
                )
            else:
                self.repository.create_log(
                    execution.id,
                    "info",
                    f"CONCLUIDA|{index}|{command}|{name}|{message}",
                )
            if progress is not None:
                progress(int((index / total) * 100), name, "Concluída")
        else:
            execution.status = "Concluída"
            execution.result = "Todas as etapas foram concluídas."

        finished = datetime.now(UTC)
        execution.finished_at = finished.replace(tzinfo=None)
        execution.duration = max(0, int((finished - started).total_seconds()))
        execution = self.repository.update_execution(execution)
        return {
            "status": execution.status,
            "execution_id": execution.id,
            "result": execution.result,
            "current_step": execution.current_step,
        }

    def _execute_step(
        self,
        step: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        command = str(step.get("command") or "")
        if bool(step.get("manual")) or command == "manual_submit_application":
            return {
                "status": "Aguardando usuário",
                "message": "Intervenção manual necessária.",
            }
        handler = self.step_handlers.get(command)
        if handler is None:
            return {
                "status": "Concluída",
                "message": "Etapa preparada no orquestrador Sprint 1.",
            }
        return handler(step, context) or {"status": "Concluída"}

    def retry_failed_step(
        self,
        execution_id: int,
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        execution = self.repository.get_execution(execution_id)
        if execution is None:
            raise ValueError("Execução não encontrada.")
        workflow = self.get_workflow(execution.workflow_id)
        if workflow is None:
            raise ValueError("Workflow não encontrado.")

        failed_logs = [
            log.message
            for log in self.repository.list_logs(execution_id)
            if log.message.startswith("FALHOU|")
        ]
        if not failed_logs:
            raise ValueError("A execução não possui etapa com falha.")

        parts = failed_logs[-1].split("|", 4)
        failed_index = int(parts[1])
        steps = self.parse_definition(workflow)["steps"]
        if failed_index < 1 or failed_index > len(steps):
            raise ValueError("A etapa com falha não existe mais no workflow.")

        step = steps[failed_index - 1]
        result = self._execute_step(step, context or {})
        self.repository.create_log(
            execution_id,
            "info",
            f"REEXECUTADA|{failed_index}|{step.get('command', '')}|"
            f"{step.get('name', '')}|{result.get('message', '')}",
        )
        return result

    def get_workflow(self, workflow_id: int) -> Workflow | None:
        return self.repository.get_workflow(workflow_id)

    def list_workflows(self) -> list[Workflow]:
        return self.repository.list_workflows()

    def list_executions(
        self,
        workflow_id: int | None = None,
        *,
        limit: int = 100,
    ) -> list[Any]:
        return self.repository.list_executions(workflow_id, limit=limit)

    def list_logs(self, execution_id: int) -> list[Any]:
        return self.repository.list_logs(execution_id)

    def latest_execution(self, workflow_id: int) -> Any | None:
        return self.repository.latest_execution(workflow_id)

    def get_execution_status(self, execution_id: int) -> dict[str, Any]:
        execution = self.repository.get_execution(execution_id)
        if execution is None:
            return {"status": "not_found"}
        return {
            "status": execution.status,
            "workflow_id": execution.workflow_id,
            "current_step": execution.current_step,
            "started_at": str(execution.started_at) if execution.started_at else None,
            "finished_at": str(execution.finished_at) if execution.finished_at else None,
        }
