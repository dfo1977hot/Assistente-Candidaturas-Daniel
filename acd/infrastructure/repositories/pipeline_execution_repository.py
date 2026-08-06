from __future__ import annotations

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.pipeline_execution import PipelineExecution


class SqlAlchemyPipelineExecutionRepository:
    """SQLite adapter for IAP execution history."""

    def save(self, execution: PipelineExecution) -> PipelineExecution:
        with database_module.SessionLocal() as session:
            session.add(execution)
            session.commit()
            session.refresh(execution)
            return execution

    def get(self, execution_id: str) -> PipelineExecution | None:
        with database_module.SessionLocal() as session:
            return session.scalar(
                select(PipelineExecution).where(PipelineExecution.execution_id == execution_id)
            )

    def list(self, limit: int = 20) -> list[PipelineExecution]:
        with database_module.SessionLocal() as session:
            statement = select(PipelineExecution).order_by(PipelineExecution.started_at.desc()).limit(limit)
            return list(session.scalars(statement).all())

    def latest(self) -> PipelineExecution | None:
        records = self.list(limit=1)
        return records[0] if records else None

    def delete_exceeding(self, maximum_records: int) -> int:
        records = self.list(limit=10_000)
        excess = records[maximum_records:]
        if not excess:
            return 0
        with database_module.SessionLocal() as session:
            for record in excess:
                session.delete(session.merge(record))
            session.commit()
        return len(excess)
