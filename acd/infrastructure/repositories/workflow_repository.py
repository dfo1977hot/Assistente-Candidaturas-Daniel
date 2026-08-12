from __future__ import annotations

from sqlalchemy import delete, select

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
            session.expunge(workflow)
            return workflow

    def update_workflow(
        self,
        workflow_id: int,
        *,
        name: str,
        description: str,
        definition: str,
        active: bool,
        version: str,
    ) -> Workflow:
        with database_module.SessionLocal() as session:
            workflow = session.get(Workflow, workflow_id)
            if workflow is None:
                raise ValueError("Workflow não encontrado.")
            workflow.name = name
            workflow.description = description
            workflow.definition = definition
            workflow.active = active
            workflow.version = version
            session.commit()
            session.refresh(workflow)
            session.expunge(workflow)
            return workflow

    def delete_workflow(self, workflow_id: int) -> bool:
        with database_module.SessionLocal() as session:
            execution_ids = list(
                session.scalars(
                    select(WorkflowExecution.id).where(
                        WorkflowExecution.workflow_id == workflow_id
                    )
                ).all()
            )
            if execution_ids:
                session.execute(
                    delete(WorkflowLog).where(
                        WorkflowLog.workflow_execution_id.in_(execution_ids)
                    )
                )
                session.execute(
                    delete(WorkflowEvent).where(
                        WorkflowEvent.workflow_execution_id.in_(execution_ids)
                    )
                )
                session.execute(
                    delete(WorkflowExecution).where(
                        WorkflowExecution.id.in_(execution_ids)
                    )
                )
            workflow = session.get(Workflow, workflow_id)
            if workflow is None:
                return False
            session.delete(workflow)
            session.commit()
            return True

    def get_workflow(self, workflow_id: int) -> Workflow | None:
        with database_module.SessionLocal() as session:
            workflow = session.get(Workflow, workflow_id)
            if workflow is not None:
                session.expunge(workflow)
            return workflow

    def list_workflows(self) -> list[Workflow]:
        with database_module.SessionLocal() as session:
            workflows = list(
                session.scalars(select(Workflow).order_by(Workflow.id.desc())).all()
            )
            for workflow in workflows:
                session.expunge(workflow)
            return workflows

    def create_execution(
        self,
        workflow_id: int,
        application_id: int | None = None,
    ) -> WorkflowExecution:
        with database_module.SessionLocal() as session:
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                application_id=application_id,
                status="created",
            )
            session.add(execution)
            session.commit()
            session.refresh(execution)
            session.expunge(execution)
            return execution

    def get_execution(self, execution_id: int) -> WorkflowExecution | None:
        with database_module.SessionLocal() as session:
            execution = session.get(WorkflowExecution, execution_id)
            if execution is not None:
                session.expunge(execution)
            return execution

    def update_execution(
        self,
        execution: WorkflowExecution,
    ) -> WorkflowExecution:
        with database_module.SessionLocal() as session:
            stored = session.get(WorkflowExecution, execution.id)
            if stored is None:
                raise ValueError("Execução de workflow não encontrada.")
            for field in (
                "status",
                "current_step",
                "started_at",
                "finished_at",
                "duration",
                "result",
                "context",
            ):
                setattr(stored, field, getattr(execution, field))
            session.commit()
            session.refresh(stored)
            session.expunge(stored)
            return stored

    def list_executions(
        self,
        workflow_id: int | None = None,
        *,
        limit: int = 100,
    ) -> list[WorkflowExecution]:
        with database_module.SessionLocal() as session:
            statement = select(WorkflowExecution)
            if workflow_id is not None:
                statement = statement.where(
                    WorkflowExecution.workflow_id == workflow_id
                )
            statement = statement.order_by(WorkflowExecution.id.desc()).limit(limit)
            executions = list(session.scalars(statement).all())
            for execution in executions:
                session.expunge(execution)
            return executions

    def latest_execution(
        self,
        workflow_id: int,
    ) -> WorkflowExecution | None:
        executions = self.list_executions(workflow_id, limit=1)
        return executions[0] if executions else None

    def create_event(
        self,
        execution_id: int,
        event_type: str,
        event_data: str,
    ) -> WorkflowEvent:
        with database_module.SessionLocal() as session:
            event = WorkflowEvent(
                workflow_execution_id=execution_id,
                event_type=event_type,
                event_data=event_data,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            session.expunge(event)
            return event

    def create_log(
        self,
        execution_id: int,
        level: str,
        message: str,
    ) -> WorkflowLog:
        with database_module.SessionLocal() as session:
            log = WorkflowLog(
                workflow_execution_id=execution_id,
                level=level,
                message=message,
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            session.expunge(log)
            return log

    def list_logs(self, execution_id: int) -> list[WorkflowLog]:
        with database_module.SessionLocal() as session:
            logs = list(
                session.scalars(
                    select(WorkflowLog)
                    .where(WorkflowLog.workflow_execution_id == execution_id)
                    .order_by(WorkflowLog.id.asc())
                ).all()
            )
            for log in logs:
                session.expunge(log)
            return logs

    def get_template(self, template_id: int) -> WorkflowTemplate | None:
        with database_module.SessionLocal() as session:
            template = session.get(WorkflowTemplate, template_id)
            if template is not None:
                session.expunge(template)
            return template

    def list_templates(self) -> list[WorkflowTemplate]:
        with database_module.SessionLocal() as session:
            templates = list(session.scalars(select(WorkflowTemplate)).all())
            for template in templates:
                session.expunge(template)
            return templates
