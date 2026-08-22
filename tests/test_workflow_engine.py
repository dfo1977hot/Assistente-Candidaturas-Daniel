from __future__ import annotations

from typing import Any

import pytest

from acd.domain.entities.workflow_execution import WorkflowExecution
from acd.domain.entities.workflow_template import WorkflowTemplate
from acd.domain.workflow.execution_context import ExecutionContext
from acd.infrastructure.repositories.workflow_repository import (
    WorkflowRepository,
)
from acd.infrastructure.workflow.command_dispatcher import (
    CommandDispatcher,
)
from acd.infrastructure.workflow.workflow_event_bus import (
    EventBus,
)
from acd.infrastructure.workflow.workflow_runner import (
    WorkflowRunner,
)
from acd.services.workflow_service import WorkflowService
from acd.services.workflow_template_service import (
    WorkflowTemplateService,
)


@pytest.fixture
def workflow_setup(monkeypatch, tmp_path):
    """
    Cria um banco SQLite temporário para os testes de Workflow.

    Mantém isolamento completo e restaura o estado do módulo database
    ao final do teste.
    """

    temp_dir = tmp_path
    db_path = str(temp_dir / "test_acd_workflow.db")

    monkeypatch.setattr(
        "acd.database.database.DATABASE_URL",
        f"sqlite:///{db_path}",
    )

    import acd.database.database as database_module
    from acd.models.base import Base

    old_engine = database_module.engine
    old_session_local = database_module.SessionLocal

    old_engine.dispose()

    database_module.engine = database_module.create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        future=True,
    )

    database_module.SessionLocal = database_module.sessionmaker(
        bind=database_module.engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    try:
        yield
    finally:
        Base.metadata.drop_all(bind=database_module.engine)
        database_module.engine.dispose()

        database_module.engine = old_engine
        database_module.SessionLocal = old_session_local


def test_workflow_service_creates_workflow(db_session):
    service = WorkflowService(repository=WorkflowRepository())

    steps = [
        {"name": "Análise", "command": "analyze_job"},
        {"name": "ATS", "command": "run_ats"},
    ]

    workflow = service.create_workflow(
        "Teste",
        "Workflow de teste",
        steps,
    )

    assert workflow is not None
    assert workflow.name == "Teste"


def test_workflow_service_executes_workflow(db_session):
    service = WorkflowService(repository=WorkflowRepository())

    steps = [
        {"name": "Análise", "command": "analyze_job"},
        {"name": "ATS", "command": "run_ats"},
    ]

    workflow = service.create_workflow(
        "Teste",
        "Workflow de teste",
        steps,
    )

    result = service.execute_workflow(workflow.id)

    assert result["status"] == "completed"


def test_event_bus_publishes_events(db_session):
    event_bus = EventBus()

    events_received: list[tuple[str, dict[str, Any]]] = []

    def handler(event_type: str, data: dict[str, Any]) -> None:
        events_received.append((event_type, data))

    event_bus.subscribe(
        "workflow_started",
        handler,
    )

    event_bus.publish(
        "workflow_started",
        {"workflow_id": 1},
    )

    assert len(events_received) == 1
    assert events_received[0][0] == "workflow_started"


def test_command_dispatcher_dispatches_commands(db_session):
    dispatcher = CommandDispatcher()

    command = dispatcher.dispatch("analyze_job")

    assert command is not None
    assert command.name() == "analyze_job"


def test_execution_context_stores_data(db_session):
    context = ExecutionContext(
        workflow_execution_id=1,
        workflow_id=1,
    )

    context.set_data("test", "value")

    assert context.get_data("test") == "value"


def test_execution_context_handles_errors(db_session):
    context = ExecutionContext(
        workflow_execution_id=1,
        workflow_id=1,
    )

    context.add_error("Test error")

    assert len(context.errors) == 1

def test_workflow_template_service_provides_templates(db_session):
    service = WorkflowTemplateService()

    templates = service.get_templates()

    assert len(templates) > 0
    assert any(
        template["name"] == "Candidatura Completa"
        for template in templates
    )


def test_workflow_template_service_creates_from_template(db_session):
    template_service = WorkflowTemplateService(
        workflow_service=WorkflowService(
            repository=WorkflowRepository(),
        ),
    )

    result = template_service.create_workflow_from_template(
        "Apenas ATS",
    )

    assert result is not None
    assert "id" in result or "error" not in result


def test_event_bus_unsubscribe_removes_handler(db_session):
    event_bus = EventBus()

    received: list[tuple[str, dict[str, Any]]] = []

    def handler(event_type: str, data: dict[str, Any]) -> None:
        received.append((event_type, data))

    event_bus.subscribe(
        "workflow_started",
        handler,
    )

    event_bus.unsubscribe(
        "workflow_started",
        handler,
    )

    event_bus.publish(
        "workflow_started",
        {"id": 1},
    )

    assert received == []


def test_event_bus_publish_without_subscribers(db_session):
    event_bus = EventBus()

    event_bus.publish(
        "unknown_event",
        {"value": 1},
    )


def test_event_bus_handler_exception_is_ignored(
    db_session,
    caplog,
):
    event_bus = EventBus()

    def failing_handler(event_type: str, data: dict[str, Any]) -> None:
        raise RuntimeError("boom")

    event_bus.subscribe(
        "workflow_started",
        failing_handler,
    )

    event_bus.publish(
        "workflow_started",
        {},
    )

    assert "Unhandled exception" in caplog.text


def test_workflow_repository_get_execution(db_session):
    """Repository must retrieve an execution by id."""

    repository = WorkflowRepository()

    workflow = repository.create_workflow(
        "Workflow",
        "Descrição",
        '{"steps": []}',
    )

    execution = repository.create_execution(workflow.id)

    loaded = repository.get_execution(execution.id)

    assert loaded is not None
    assert loaded.id == execution.id
    assert loaded.workflow_id == workflow.id


def test_workflow_repository_create_event(db_session):
    """Repository must persist workflow events."""

    repository = WorkflowRepository()

    workflow = repository.create_workflow(
        "Workflow",
        "Descrição",
        '{"steps": []}',
    )

    execution = repository.create_execution(workflow.id)

    event = repository.create_event(
        execution.id,
        "workflow_started",
        '{"step": 1}',
    )

    assert event.id is not None
    assert event.workflow_execution_id == execution.id
    assert event.event_type == "workflow_started"


def test_workflow_repository_create_log(db_session):
    """Repository must persist workflow logs."""

    repository = WorkflowRepository()

    workflow = repository.create_workflow(
        "Workflow",
        "Descrição",
        '{"steps": []}',
    )

    execution = repository.create_execution(workflow.id)

    log = repository.create_log(
        execution.id,
        "INFO",
        "Workflow iniciado.",
    )

    assert log.id is not None
    assert log.workflow_execution_id == execution.id
    assert log.level == "INFO"
    assert log.message == "Workflow iniciado."


def test_workflow_repository_get_template_none(db_session):
    """Unknown template ids must return None."""

    repository = WorkflowRepository()

    template = repository.get_template(999999)

    assert template is None


def test_workflow_repository_list_templates(db_session):
    """Repository must list workflow templates."""

    import acd.database.database as database_module

    repository = WorkflowRepository()

    with database_module.SessionLocal() as session:
        session.add(
            WorkflowTemplate(
                name="Template Teste",
                description="Template de teste",
                definition='{"steps": []}',
            )
        )
        session.commit()

    templates = repository.list_templates()

    assert len(templates) >= 1
    assert any(
        template.name == "Template Teste"
        for template in templates
    )


def test_runner_returns_error_when_workflow_not_found(db_session):
    """Runner must return an error when workflow does not exist."""

    repository = WorkflowRepository()
    runner = WorkflowRunner(repository=repository)

    execution = WorkflowExecution(
        id=1,
        workflow_id=999999,
        application_id=None,
        status="created",
    )

    result = runner.run(execution)

    assert result["status"] == "error"
    assert result["message"] == "Workflow not found"


def test_runner_returns_error_when_definition_is_invalid(db_session):
    """Runner must reject invalid workflow definitions."""

    repository = WorkflowRepository()

    workflow = repository.create_workflow(
        "Workflow",
        "Descrição",
        "{invalid json}",
    )

    execution = repository.create_execution(workflow.id)

    runner = WorkflowRunner(repository=repository)

    result = runner.run(execution)

    assert result["status"] == "error"
    assert result["message"] == "Invalid workflow definition"


def test_runner_fails_when_command_is_not_found(db_session):
    """Runner must fail when dispatcher cannot resolve a command."""

    repository = WorkflowRepository()

    workflow = repository.create_workflow(
        "Workflow",
        "Descrição",
        '{"steps":[{"name":"Teste","command":"inexistente"}]}',
    )

    execution = repository.create_execution(workflow.id)

    runner = WorkflowRunner(repository=repository)

    result = runner.run(execution)

    assert result["status"] == "failed"

    execution_db = repository.get_execution(execution.id)
    assert execution_db is not None
    assert execution_db.status == "failed"


def test_runner_fails_when_command_raises_exception(db_session, monkeypatch):
    """Runner must fail when a command raises an exception."""

    class FailingCommand:
        def execute(self, context):
            raise RuntimeError("boom")

    repository = WorkflowRepository()

    workflow = repository.create_workflow(
        "Workflow",
        "Descrição",
        '{"steps":[{"name":"Teste","command":"falha"}]}',
    )

    execution = repository.create_execution(workflow.id)

    runner = WorkflowRunner(repository=repository)

    monkeypatch.setattr(
        runner.dispatcher,
        "dispatch",
        lambda _: FailingCommand(),
    )

    result = runner.run(execution)

    assert result["status"] == "failed"

    execution_db = repository.get_execution(execution.id)
    assert execution_db is not None
    assert execution_db.status == "failed"

def test_runner_does_not_complete_after_command_failure(
    db_session,
    monkeypatch,
):
    """A failed workflow must not publish completion."""

    class FailingCommand:
        def execute(self, context):
            raise RuntimeError("boom")

    repository = WorkflowRepository()

    workflow = repository.create_workflow(
        "Workflow",
        "Descrição",
        '{"steps":[{"name":"Teste","command":"falha"}]}',
    )

    execution = repository.create_execution(workflow.id)

    completed_events = []

    runner = WorkflowRunner(repository=repository)

    def publish(event, payload):
        if event == "workflow_completed":
            completed_events.append(payload)

    monkeypatch.setattr(
        runner.event_bus,
        "publish",
        publish,
    )

    monkeypatch.setattr(
        runner.dispatcher,
        "dispatch",
        lambda _: FailingCommand(),
    )

    result = runner.run(execution)

    assert result["status"] == "failed"
    assert completed_events == []