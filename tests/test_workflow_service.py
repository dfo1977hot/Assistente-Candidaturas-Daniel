from __future__ import annotations

import json

import pytest

from acd.services.workflow_service import WorkflowService


class DummyExecution:
    def __init__(self):
        self.id = 1
        self.workflow_id = 10
        self.application_id = 99
        self.status = "completed"
        self.current_step = 2
        self.started_at = None
        self.finished_at = None


class DummyWorkflow:
    def __init__(self):
        self.id = 10
        self.name = "Workflow Teste"


class FakeRepository:
    def __init__(self):
        self.workflow = DummyWorkflow()
        self.execution = DummyExecution()

    def create_workflow(
        self,
        name,
        description,
        definition,
        *,
        version="1",
    ):
        self.last_definition = definition
        self.last_version = version
        self.workflow.name = name
        return self.workflow

    def create_execution(
        self,
        workflow_id,
        application_id,
    ):
        self.execution.workflow_id = workflow_id
        self.execution.application_id = application_id
        return self.execution

    def get_workflow(self, workflow_id):
        if workflow_id == self.workflow.id:
            return self.workflow
        return None

    def list_workflows(self):
        return [self.workflow]

    def get_execution(self, execution_id):
        if execution_id == self.execution.id:
            return self.execution
        return None


class FakeRunner:
    def __init__(self):
        self.last_execution = None

    def run(self, execution):
        self.last_execution = execution
        return {
            "status": "completed",
            "execution_id": execution.id,
        }


@pytest.fixture
def service():
    repository = FakeRepository()
    runner = FakeRunner()

    service = WorkflowService(
        repository=repository,
        runner=runner,
    )

    return service, repository, runner


def test_create_workflow(service):
    workflow_service, repository, _ = service

    workflow = workflow_service.create_workflow(
        "Meu Workflow",
        "Descrição",
        [{"name": "Passo"}],
    )

    definition = json.loads(repository.last_definition)

    assert workflow.name == "Meu Workflow"
    assert definition["steps"][0]["name"] == "Passo"


def test_create_workflow_version(service):
    workflow_service, repository, _ = service

    workflow_service.create_workflow(
        "Workflow",
        "Descrição",
        [],
        version="2",
    )

    assert repository.last_version == "2"


def test_execute_workflow(service):
    workflow_service, _, runner = service

    result = workflow_service.execute_workflow(
        10,
        application_id=50,
    )

    assert result["status"] == "completed"
    assert runner.last_execution.application_id == 50


def test_get_workflow(service):
    workflow_service, _, _ = service

    workflow = workflow_service.get_workflow(10)

    assert workflow is not None
    assert workflow.id == 10


def test_get_unknown_workflow(service):
    workflow_service, _, _ = service

    assert workflow_service.get_workflow(999) is None


def test_list_workflows(service):
    workflow_service, _, _ = service

    workflows = workflow_service.list_workflows()

    assert len(workflows) == 1
    assert workflows[0].id == 10


def test_get_execution_status(service):
    workflow_service, _, _ = service

    status = workflow_service.get_execution_status(1)

    assert status["status"] == "completed"
    assert status["workflow_id"] == 10
    assert status["current_step"] == 2


def test_get_execution_status_not_found(service):
    workflow_service, repository, _ = service

    repository.execution.id = 2

    status = workflow_service.get_execution_status(999)

    assert status == {"status": "not_found"}