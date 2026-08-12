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
