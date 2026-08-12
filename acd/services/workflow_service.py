from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import json
from time import monotonic
from typing import Any

from acd.domain.entities.workflow import Workflow
from acd.infrastructure.repositories.workflow_repository import WorkflowRepository
from acd.infrastructure.workflow.workflow_event_bus import EventBus
from acd.infrastructure.workflow.workflow_runner import WorkflowRunner
from acd.services.workflow_condition_evaluator import WorkflowConditionEvaluator
from acd.services.workflow_step_registry import WorkflowStepRegistry

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
        step_registry: WorkflowStepRegistry | None = None,
        condition_evaluator: WorkflowConditionEvaluator | None = None,
    ) -> None:
        self.repository = repository or WorkflowRepository()
        self.event_bus = event_bus or EventBus()
        self.runner = runner or WorkflowRunner(self.repository, self.event_bus)
        self.step_registry = step_registry or WorkflowStepRegistry(step_handlers)
        self.condition_evaluator = condition_evaluator or WorkflowConditionEvaluator()

    @staticmethod
    def _definition(
        steps: list[dict[str, Any]],
        *,
        trigger: str = "Execução manual",
        schedule: dict[str, Any] | None = None,
        target_status: str = "",
    ) -> str:
        payload: dict[str, Any] = {"trigger": trigger, "steps": steps}
        if schedule is not None:
            payload["schedule"] = schedule
        if target_status:
            payload["target_status"] = target_status
        return json.dumps(
            payload,
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
            "schedule": value.get("schedule"),
            "target_status": str(value.get("target_status") or ""),
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
        schedule: dict[str, Any] | None = None,
        target_status: str = "",
    ) -> Workflow:
        workflow = self.repository.create_workflow(
            name,
            description,
            self._definition(
                steps, trigger=trigger, schedule=schedule, target_status=target_status
            ),
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
        schedule: dict[str, Any] | None = None,
        target_status: str = "",
    ) -> Workflow:
        if workflow_id is None:
            return self.create_workflow(
                name,
                description,
                steps,
                version=version,
                trigger=trigger,
                active=active,
                schedule=schedule,
                target_status=target_status,
            )
        return self.repository.update_workflow(
            workflow_id,
            name=name,
            description=description,
            definition=self._definition(
                steps, trigger=trigger, schedule=schedule, target_status=target_status
            ),
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
            schedule=definition.get("schedule"),
            target_status=definition.get("target_status", ""),
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
        execution_id: int | None = None,
        start_index: int = 1,
    ) -> dict[str, Any]:
        """Run a Sprint 1 workflow step-by-step with progress and history."""
        workflow = self.get_workflow(workflow_id)
        if workflow is None:
            raise ValueError("Workflow não encontrado.")
        if not workflow.active:
            raise ValueError("O workflow está inativo.")

        definition = self.parse_definition(workflow)
        steps = definition["steps"]
        execution = (
            self.repository.get_execution(execution_id)
            if execution_id is not None
            else self.repository.create_execution(workflow_id)
        )
        if execution is None:
            raise ValueError("Execução não encontrada.")
        execution.status = "Em execução"
        execution.started_at = datetime.now(UTC).replace(tzinfo=None)
        if context is None and execution.context:
            execution_context = json.loads(execution.context)
        else:
            execution_context = dict(context or {})
        execution.context = json.dumps(execution_context, ensure_ascii=False)
        execution = self.repository.update_execution(execution)
        origin = str(execution_context.get("trigger_origin") or "manual")
        trigger = str(execution_context.get("trigger") or definition["trigger"])
        self.repository.create_log(
            execution.id, "info", f"Workflow iniciado.|origin={origin}|trigger={trigger}"
        )

        if not steps:
            execution.status = "Concluída"
            execution.result = "Workflow sem etapas."
            execution.finished_at = datetime.now(UTC).replace(tzinfo=None)
            return self.repository.update_execution(execution).__dict__

        started = datetime.now(UTC)
        total = len(steps)

        for index in range(start_index, total + 1):
            step = steps[index - 1]
            name = str(step.get("name") or f"Etapa {index}")
            command = str(step.get("command") or "")
            condition = step.get("condition")
            if isinstance(condition, dict) and condition.get("field"):
                evaluated = self.condition_evaluator.evaluate(condition, execution_context)
                self.repository.create_log(
                    execution.id,
                    "info",
                    "CONDICAO|"
                    f"{index}|{evaluated.field}|{evaluated.operator}|"
                    f"expected={evaluated.expected}|observed={evaluated.observed}|"
                    f"matched={evaluated.matched}",
                )
                if not evaluated.matched:
                    execution.current_step = index
                    execution.result = "Etapa ignorada por condição falsa."
                    self.repository.create_log(
                        execution.id,
                        "info",
                        f"IGNORADA|{index}|{command}|condição falsa",
                    )
                    if condition.get("on_false") == "Encerrar workflow":
                        execution.status = "Concluída"
                        break
                    continue
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

            step_started = monotonic()
            try:
                result = self._execute_step(step, execution_context)
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
            context_updates = (result or {}).get("context_updates") or {}
            if not isinstance(context_updates, dict):
                raise TypeError("context_updates deve ser um objeto serializável.")
            execution_context.update(context_updates)
            execution.context = json.dumps(execution_context, ensure_ascii=False)
            execution = self.repository.update_execution(execution)
            duration_ms = int((monotonic() - step_started) * 1000)
            targets = ",".join(
                f"{key}={execution_context[key]}"
                for key in ("job_id", "application_id", "curriculum_id")
                if execution_context.get(key) is not None
            )
            summary = f"{message}|targets={targets}|duration_ms={duration_ms}"
            normalized = status.casefold()
            if normalized in {"falhou", "failed"}:
                execution.status = "Falhou"
                execution.result = message or f"Falha em: {name}"
                self.repository.create_log(
                    execution.id,
                    "error",
                    f"FALHOU|{index}|{command}|{name}|{summary}",
                )
                if progress is not None:
                    progress(int((index / total) * 100), name, "Falhou")
                break
            if normalized in {"aguardando usuário", "awaiting_user", "awaiting user"}:
                execution.status = "Aguardando usuário"
                execution.result = message or f"Aguardando usuário em: {name}"
                self.repository.create_log(
                    execution.id,
                    "info",
                    f"AGUARDANDO|{index}|{command}|{name}|{summary}",
                )
                if progress is not None:
                    progress(int((index / total) * 100), name, "Aguardando usuário")
                break
            if normalized in {"ignorada", "skipped"}:
                self.repository.create_log(
                    execution.id,
                    "info",
                    f"IGNORADA|{index}|{command}|{name}|{summary}",
                )
            else:
                self.repository.create_log(
                    execution.id,
                    "info",
                    f"CONCLUIDA|{index}|{command}|{name}|{summary}",
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
        if self.step_registry.requires_job(command) and not context.get("job_id"):
            raise ValueError("Selecione uma vaga antes de executar esta etapa.")
        handler = self.step_registry.resolve(command)
        if handler is None:
            return {
                "status": "Ignorada",
                "message": "Esta etapa ainda não possui integração produtiva.",
                "context_updates": {},
            }
        return handler(step, context) or {
            "status": "Concluída",
            "context_updates": {},
        }

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
        if context is None:
            try:
                stored_context = json.loads(execution.context or "{}")
            except (TypeError, ValueError, json.JSONDecodeError):
                stored_context = {}
        else:
            stored_context = dict(context)
        result = self._execute_step(step, stored_context)
        stored_context.update(result.get("context_updates") or {})
        execution.context = json.dumps(stored_context, ensure_ascii=False)
        self.repository.update_execution(execution)
        self.repository.create_log(
            execution_id,
            "info",
            f"REEXECUTADA|{failed_index}|{step.get('command', '')}|"
            f"{step.get('name', '')}|{result.get('message', '')}",
        )
        return result

    def resume_execution(
        self,
        execution_id: int,
        *,
        from_failed_step: bool = False,
        progress: ProgressCallback | None = None,
        cancel_requested: CancelCallback | None = None,
    ) -> dict[str, Any]:
        execution = self.repository.get_execution(execution_id)
        if execution is None:
            raise ValueError("Execução não encontrada.")
        allowed = {"Aguardando usuário", "Falhou"}
        if execution.status not in allowed:
            raise ValueError("A execução não está aguardando usuário nem com falha.")
        start_index = execution.current_step if from_failed_step else execution.current_step + 1
        return self.execute_assisted(
            execution.workflow_id,
            execution_id=execution.id,
            start_index=start_index,
            progress=progress,
            cancel_requested=cancel_requested,
        )

    def has_idempotency_key(self, key: str) -> bool:
        for execution in self.list_executions(limit=1000):
            try:
                context = json.loads(execution.context or "{}")
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if context.get("idempotency_key") == key:
                return True
        return False

    def dashboard_summary(self) -> dict[str, Any]:
        executions = self.list_executions(limit=200)
        return {
            "active_workflows": sum(1 for item in self.list_workflows() if item.active),
            "running": sum(1 for item in executions if item.status == "Em execução"),
            "recent_failures": [item for item in executions if item.status == "Falhou"][:10],
            "awaiting_user": [
                item for item in executions if item.status == "Aguardando usuário"
            ][:10],
        }

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
