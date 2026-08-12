from __future__ import annotations

from datetime import datetime
import json
from types import SimpleNamespace

import pytest

from acd.services.application_service import ApplicationService
from acd.services.job_service import JobService
from acd.services.workflow_condition_evaluator import WorkflowConditionEvaluator
from acd.services.workflow_scheduler_service import WorkflowSchedulerService
from acd.services.workflow_trigger_dispatcher import WorkflowTriggerDispatcher


@pytest.mark.parametrize(
    ("operator", "observed", "expected", "matched"),
    [
        ("==", "Ativa", "Ativa", True),
        ("!=", "Ativa", "Fechada", True),
        (">", 80, 75, True),
        (">=", 75, 75, True),
        ("<", 70, 75, True),
        ("<=", 75, 75, True),
        ("contém", "Python e SQL", "python", True),
        ("não contém", "Python e SQL", "Java", True),
        ("está vazio", "", None, True),
        ("não está vazio", "https://example.test", None, True),
    ],
)
def test_condition_evaluator_supports_allow_list(
    operator, observed, expected, matched
) -> None:
    evaluator = WorkflowConditionEvaluator()
    result = evaluator.evaluate(
        {"field": "application_url", "operator": operator, "value": expected},
        {"application_url": observed},
    )
    assert result.matched is matched


def test_condition_evaluator_has_no_dynamic_eval() -> None:
    import inspect

    source = inspect.getsource(WorkflowConditionEvaluator)
    assert "eval(" not in source
    with pytest.raises(ValueError, match="Campo"):
        WorkflowConditionEvaluator().evaluate(
            {"field": "__import__", "operator": "==", "value": "x"}, {}
        )


@pytest.mark.parametrize(
    ("recurrence", "expected"),
    [
        ("Uma vez", None),
        ("Diariamente", datetime(2026, 8, 13, 9, 30)),
        ("Semanalmente", datetime(2026, 8, 19, 9, 30)),
        ("Mensalmente", datetime(2026, 9, 12, 9, 30)),
    ],
)
def test_scheduler_calculates_next_run(recurrence, expected) -> None:
    scheduled = datetime(2026, 8, 12, 9, 30)
    assert WorkflowSchedulerService.calculate_next_run(
        scheduled, recurrence, after=scheduled
    ) == expected


class WorkflowServiceStub:
    def __init__(self, workflows):
        self.workflows = workflows
        self.executions = []
        self.keys = set()
        self.saved = []

    def list_workflows(self):
        return self.workflows

    def parse_definition(self, workflow):
        return json.loads(workflow.definition)

    def has_idempotency_key(self, key):
        return key in self.keys

    def execute_assisted(self, workflow_id, *, context):
        self.keys.add(context["idempotency_key"])
        self.executions.append((workflow_id, context))
        return {"status": "Concluída", "execution_id": len(self.executions)}

    def save_workflow(self, workflow_id, **values):
        self.saved.append((workflow_id, values))


def workflow(trigger, **extra):
    return SimpleNamespace(
        id=1,
        active=True,
        name="Fluxo",
        description="",
        version="1",
        definition=json.dumps({"trigger": trigger, "steps": [], **extra}),
    )


def test_trigger_dispatcher_filters_status_and_deduplicates_occurrence() -> None:
    service = WorkflowServiceStub(
        [workflow("Mudança de status", target_status="Em Triagem")]
    )
    dispatcher = WorkflowTriggerDispatcher(service)
    ignored = dispatcher.dispatch(
        "application.status_changed",
        {"application_id": 2, "application_status": "Aplicada", "occurrence_id": "a"},
    )
    assert ignored == []
    payload = {
        "application_id": 2,
        "application_status": "Em Triagem",
        "occurrence_id": "b",
    }
    assert len(dispatcher.dispatch("application.status_changed", payload)) == 1
    assert dispatcher.dispatch("application.status_changed", payload) == []


@pytest.mark.parametrize(
    ("event_type", "trigger"),
    [
        ("job.created", "Vaga criada manualmente"),
        ("job.imported", "Vaga importada"),
        ("application.created", "Candidatura criada"),
    ],
)
def test_productive_events_dispatch_compatible_workflow(event_type, trigger) -> None:
    service = WorkflowServiceStub([workflow(trigger)])
    result = WorkflowTriggerDispatcher(service).dispatch(
        event_type, {"entity_id": 3, "occurrence_id": "event-1"}
    )
    assert result[0]["status"] == "Concluída"


def test_due_schedule_runs_once_and_is_persistently_advanced() -> None:
    scheduled = "2026-08-11T09:00:00"
    item = workflow(
        "Agendado",
        schedule={
            "scheduled_at": scheduled,
            "next_run_at": scheduled,
            "last_run_at": None,
            "recurrence": "Diariamente",
            "active": True,
        },
    )
    service = WorkflowServiceStub([item])
    scheduler = WorkflowSchedulerService(service)
    now = datetime(2026, 8, 12, 10, 0)
    assert len(scheduler.run_due(now)) == 1
    assert service.saved[0][1]["schedule"]["last_run_at"] == now.isoformat()
    assert service.saved[0][1]["schedule"]["next_run_at"] == "2026-08-13T09:00:00"


class JobRepositoryStub:
    def url_exists(self, *_args, **_kwargs):
        return False

    def create(self, job):
        job.id = 41
        return job


def test_job_service_emits_manual_and_imported_events() -> None:
    events = []
    service = JobService(JobRepositoryStub(), lambda name, data: events.append((name, data)))
    service.create_job(company_id=1, title="Manual")
    service.create_job(company_id=1, title="Importada", imported=True)
    assert [event[0] for event in events] == ["job.created", "job.imported"]


class ApplicationRepositoryStub:
    def __init__(self):
        self.row = None

    def create(self, application):
        application.id = 51
        self.row = application
        return application

    def add_event(self, *_args):
        return None

    def get_by_id(self, application_id):
        return self.row if application_id == 51 else None

    def change_status(self, application_id, status, **_kwargs):
        self.row.status = status
        return self.row


def test_application_service_emits_created_and_status_events() -> None:
    events = []
    service = ApplicationService(
        ApplicationRepositoryStub(), lambda name, data: events.append((name, data))
    )
    created = service.create_application(job_id=7, company_id=3)
    service.change_status(created.id, "Preparando Currículo")
    assert [event[0] for event in events] == [
        "application.created",
        "application.status_changed",
    ]
