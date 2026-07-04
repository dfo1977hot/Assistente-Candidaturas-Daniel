import os
import json
import tempfile

import pytest

from acd.services.workflow_service import WorkflowService
from acd.services.workflow_template_service import WorkflowTemplateService
from acd.infrastructure.repositories.workflow_repository import WorkflowRepository
from acd.infrastructure.workflow.event_bus import EventBus
from acd.infrastructure.workflow.command_dispatcher import CommandDispatcher
from acd.domain.workflow.execution_context import ExecutionContext


@pytest.fixture
def workflow_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-workflow-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd_workflow.db")
    monkeypatch.setattr(
        "acd.database.database.DATABASE_URL",
        f"sqlite:///{db_path}",
    )

    import acd.database.database as database_module

    database_module.engine.dispose()
    database_module.engine = database_module.create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        future=True,
    )
    database_module.SessionLocal = database_module.sessionmaker(
        bind=database_module.engine,
        autoflush=False,
        autocommit=False,
    )

    from acd.models.base import Base

    import acd.domain.entities.workflow
    import acd.domain.entities.workflow_step
    import acd.domain.entities.workflow_execution
    import acd.domain.entities.workflow_event
    import acd.domain.entities.workflow_log
    import acd.domain.entities.workflow_template

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    yield

    Base.metadata.drop_all(bind=database_module.engine)


def test_workflow_service_creates_workflow(workflow_setup):
    service = WorkflowService(repository=WorkflowRepository())
    steps = [{"name": "Análise", "command": "analyze_job"}, {"name": "ATS", "command": "run_ats"}]
    workflow = service.create_workflow("Teste", "Workflow de teste", steps)
    assert workflow is not None
    assert workflow.name == "Teste"


def test_workflow_service_executes_workflow(workflow_setup):
    service = WorkflowService(repository=WorkflowRepository())
    steps = [{"name": "Análise", "command": "analyze_job"}, {"name": "ATS", "command": "run_ats"}]
    workflow = service.create_workflow("Teste", "Workflow de teste", steps)
    result = service.execute_workflow(workflow.id)
    assert result["status"] == "completed"


def test_event_bus_publishes_events(workflow_setup):
    event_bus = EventBus()
    events_received = []

    def handler(event_type, data):
        events_received.append((event_type, data))

    event_bus.subscribe("workflow_started", handler)
    event_bus.publish("workflow_started", {"workflow_id": 1})
    assert len(events_received) == 1
    assert events_received[0][0] == "workflow_started"


def test_command_dispatcher_dispatches_commands(workflow_setup):
    dispatcher = CommandDispatcher()
    command = dispatcher.dispatch("analyze_job")
    assert command is not None
    assert command.name() == "analyze_job"


def test_execution_context_stores_data(workflow_setup):
    context = ExecutionContext(workflow_execution_id=1, workflow_id=1)
    context.set_data("test", "value")
    assert context.get_data("test") == "value"


def test_execution_context_handles_errors(workflow_setup):
    context = ExecutionContext(workflow_execution_id=1, workflow_id=1)
    context.add_error("Test error")
    assert len(context.errors) == 1


def test_workflow_template_service_provides_templates(workflow_setup):
    service = WorkflowTemplateService()
    templates = service.get_templates()
    assert len(templates) > 0
    assert any(t["name"] == "Candidatura Completa" for t in templates)


def test_workflow_template_service_creates_from_template(workflow_setup):
    template_service = WorkflowTemplateService(workflow_service=WorkflowService(repository=WorkflowRepository()))
    result = template_service.create_workflow_from_template("Apenas ATS")
    assert result is not None
    assert "id" in result or "error" not in result
