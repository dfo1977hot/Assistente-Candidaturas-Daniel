from __future__ import annotations

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.workflow import Workflow
from acd.domain.entities.workflow_event import WorkflowEvent
from acd.domain.entities.workflow_execution import WorkflowExecution
from acd.domain.entities.workflow_log import WorkflowLog
from acd.domain.entities.workflow_template import WorkflowTemplate


class WorkflowRepository:
    """Repository for workflow persistence."""

    def create_workflow(
        self,
        name: str,
        description: str,
        definition: str,
        *,
        version: str = "1",
    ) -> Workflow:
        """Create a workflow."""

        with database_module.SessionLocal() as session:
            workflow = Workflow(
                name=name,
                description=description,
                definition=definition,
                version=version,
            )

            session.add(workflow)
            session.commit()
            session.refresh(workflow)

            return workflow

    def get_workflow(
        self,
        workflow_id: int,
    ) -> Workflow | None:
        """Return a workflow by id."""

        with database_module.SessionLocal() as session:
            return session.get(Workflow, workflow_id)

    def list_workflows(self) -> list[Workflow]:
        """Return all workflows."""

        with database_module.SessionLocal() as session:
            return list(session.scalars(select(Workflow)).all())

    def create_execution(
        self,
        workflow_id: int,
        application_id: int | None = None,
    ) -> WorkflowExecution:
        """Create a workflow execution."""

        with database_module.SessionLocal() as session:
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                application_id=application_id,
                status="created",
            )

            session.add(execution)
            session.commit()
            session.refresh(execution)

            return execution

    def get_execution(
        self,
        execution_id: int,
    ) -> WorkflowExecution | None:
        """Return a workflow execution by id."""

        with database_module.SessionLocal() as session:
            return session.get(WorkflowExecution, execution_id)

    def update_execution(
        self,
        execution: WorkflowExecution,
    ) -> WorkflowExecution:
        """Persist execution changes."""

        with database_module.SessionLocal() as session:
            session.add(execution)
            session.commit()
            session.refresh(execution)

            return execution

    def create_event(
        self,
        execution_id: int,
        event_type: str,
        event_data: str,
    ) -> WorkflowEvent:
        """Create a workflow event."""

        with database_module.SessionLocal() as session:
            event = WorkflowEvent(
                workflow_execution_id=execution_id,
                event_type=event_type,
                event_data=event_data,
            )

            session.add(event)
            session.commit()
            session.refresh(event)

            return event

    def create_log(
        self,
        execution_id: int,
        level: str,
        message: str,
    ) -> WorkflowLog:
        """Create a workflow log."""

        with database_module.SessionLocal() as session:
            log = WorkflowLog(
                workflow_execution_id=execution_id,
                level=level,
                message=message,
            )

            session.add(log)
            session.commit()
            session.refresh(log)

            return log

    def get_template(
        self,
        template_id: int,
    ) -> WorkflowTemplate | None:
        """Return a workflow template by id."""

        with database_module.SessionLocal() as session:
            return session.get(WorkflowTemplate, template_id)

    def list_templates(self) -> list[WorkflowTemplate]:
        """Return all workflow templates."""

        with database_module.SessionLocal() as session:
            return list(session.scalars(select(WorkflowTemplate)).all())