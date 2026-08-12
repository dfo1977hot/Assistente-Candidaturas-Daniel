from __future__ import annotations

import json
from types import SimpleNamespace

from acd.services.workflow_service import WorkflowService


class FakeRepository:
    def __init__(self):
        self.workflow = SimpleNamespace(
            id=1,
            name="Preparação",
            description="",
            definition=json.dumps(
                {
                    "trigger": "Execução manual",
                    "steps": [
                        {"name": "A", "command": "a"},
                        {
                            "name": "Final",
                            "command": "manual_submit_application",
                            "manual": True,
                        },
                    ],
                }
            ),
            version="1",
            active=True,
        )
        self.execution = SimpleNamespace(
            id=10,
            workflow_id=1,
            application_id=None,
            status="created",
            current_step=0,
            started_at=None,
            finished_at=None,
            duration=0,
            result="",
            context="",
            created_at=None,
        )
        self.logs = []

    def get_workflow(self, workflow_id):
        return self.workflow if workflow_id == 1 else None

    def create_execution(self, workflow_id, application_id=None):
        self.execution.workflow_id = workflow_id
        return self.execution

    def get_execution(self, execution_id):
        return self.execution if execution_id == self.execution.id else None

    def update_execution(self, execution):
        return execution

    def create_log(self, execution_id, level, message):
        self.logs.append(SimpleNamespace(level=level, message=message))
        return self.logs[-1]

    def list_logs(self, execution_id):
        return self.logs

    def latest_execution(self, workflow_id):
        return None

    def list_executions(self, workflow_id=None, limit=100):
        return [self.execution]


class FakeRunner:
    def run(self, execution):
        return {"status": "completed", "execution_id": execution.id}


def test_assisted_execution_stops_at_manual_checkpoint():
    repository = FakeRepository()
    service = WorkflowService(repository=repository, runner=FakeRunner())
    result = service.execute_assisted(1)
    assert result["status"] == "Aguardando usuário"
    assert repository.execution.current_step == 2


def test_definition_exposes_trigger_and_steps():
    repository = FakeRepository()
    service = WorkflowService(repository=repository, runner=FakeRunner())
    definition = service.parse_definition(repository.workflow)
    assert definition["trigger"] == "Execução manual"
    assert len(definition["steps"]) == 2


def test_assisted_execution_persists_context_updates():
    repository = FakeRepository()
    repository.workflow.definition = json.dumps(
        {"steps": [{"name": "Atualizar", "command": "update"}]}
    )
    service = WorkflowService(
        repository=repository,
        runner=FakeRunner(),
        step_handlers={
            "update": lambda _step, _context: {
                "status": "Concluída",
                "message": "Atualizado",
                "context_updates": {"curriculum_id": 42},
            }
        },
    )
    service.execute_assisted(1, context={"job_id": 7})
    assert json.loads(repository.execution.context) == {
        "job_id": 7,
        "curriculum_id": 42,
    }


def test_missing_job_context_stops_dependent_step():
    repository = FakeRepository()
    repository.workflow.definition = json.dumps(
        {"steps": [{"name": "Vaga", "command": "verify_job"}]}
    )
    service = WorkflowService(repository=repository, runner=FakeRunner())
    result = service.execute_assisted(1)
    assert result["status"] == "Falhou"
    assert "Selecione uma vaga" in result["result"]


def test_structured_failure_stops_following_steps_and_can_be_retried():
    repository = FakeRepository()
    repository.workflow.definition = json.dumps(
        {
            "steps": [
                {"name": "Falha", "command": "fail"},
                {"name": "Não executar", "command": "next"},
            ]
        }
    )
    calls = []

    def fail(_step, _context):
        calls.append("fail")
        return {"status": "Falhou", "message": "indisponível"}

    service = WorkflowService(
        repository=repository,
        runner=FakeRunner(),
        step_handlers={"fail": fail, "next": lambda *_args: calls.append("next")},
    )
    result = service.execute_assisted(1)
    assert result["status"] == "Falhou"
    assert calls == ["fail"]
    assert service.retry_failed_step(10)["status"] == "Falhou"
    assert calls == ["fail", "fail"]


def test_cancellation_keeps_execution_history_consistent():
    repository = FakeRepository()
    service = WorkflowService(repository=repository, runner=FakeRunner())
    result = service.execute_assisted(1, cancel_requested=lambda: True)
    assert result["status"] == "Cancelada"
    assert repository.execution.current_step == 0
    assert any(log.message.startswith("CANCELADA|") for log in repository.logs)


def test_false_condition_skips_step_and_continues():
    repository = FakeRepository()
    repository.workflow.definition = json.dumps(
        {
            "steps": [
                {
                    "name": "Condicional",
                    "command": "first",
                    "condition": {
                        "field": "fit_score",
                        "operator": ">=",
                        "value": 75,
                        "on_false": "Continuar",
                    },
                },
                {"name": "Final", "command": "second"},
            ]
        }
    )
    calls = []
    service = WorkflowService(
        repository=repository,
        runner=FakeRunner(),
        step_handlers={
            "first": lambda *_args: calls.append("first"),
            "second": lambda *_args: calls.append("second"),
        },
    )
    result = service.execute_assisted(1, context={"fit_score": 70})
    assert result["status"] == "Concluída"
    assert calls == ["second"]
    assert any(log.message.startswith("CONDICAO|") for log in repository.logs)


def test_resume_after_manual_checkpoint_does_not_repeat_completed_steps():
    repository = FakeRepository()
    calls = []
    repository.workflow.definition = json.dumps(
        {
            "steps": [
                {"name": "Primeira", "command": "first"},
                {"name": "Manual", "command": "manual_submit_application"},
                {"name": "Terceira", "command": "third"},
            ]
        }
    )
    service = WorkflowService(
        repository=repository,
        runner=FakeRunner(),
        step_handlers={
            "first": lambda *_args: calls.append("first"),
            "third": lambda *_args: calls.append("third"),
        },
    )
    assert service.execute_assisted(1)["status"] == "Aguardando usuário"
    assert calls == ["first"]
    assert service.resume_execution(10)["status"] == "Concluída"
    assert calls == ["first", "third"]


def test_false_condition_can_end_workflow_without_running_later_steps():
    repository = FakeRepository()
    calls = []
    repository.workflow.definition = json.dumps(
        {
            "steps": [
                {
                    "name": "Limiar",
                    "command": "first",
                    "condition": {
                        "field": "fit_score",
                        "operator": ">=",
                        "value": 75,
                        "on_false": "Encerrar workflow",
                    },
                },
                {"name": "Nunca", "command": "second"},
            ]
        }
    )
    service = WorkflowService(
        repository=repository,
        runner=FakeRunner(),
        step_handlers={
            "first": lambda *_args: calls.append("first"),
            "second": lambda *_args: calls.append("second"),
        },
    )
    result = service.execute_assisted(1, context={"fit_score": 50})
    assert result["status"] == "Concluída"
    assert calls == []


def test_resume_from_failure_reexecutes_failed_step_then_continues():
    repository = FakeRepository()
    calls = []
    repository.workflow.definition = json.dumps(
        {
            "steps": [
                {"name": "Falha", "command": "recover"},
                {"name": "Final", "command": "final"},
            ]
        }
    )

    def recover(*_args):
        calls.append("recover")
        if calls.count("recover") == 1:
            return {"status": "Falhou", "message": "temporária"}
        return {"status": "Concluída"}

    service = WorkflowService(
        repository=repository,
        runner=FakeRunner(),
        step_handlers={
            "recover": recover,
            "final": lambda *_args: calls.append("final"),
        },
    )
    assert service.execute_assisted(1)["status"] == "Falhou"
    assert service.resume_execution(10, from_failed_step=True)["status"] == "Concluída"
    assert calls == ["recover", "recover", "final"]
