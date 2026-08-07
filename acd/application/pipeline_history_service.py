from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import Any

from acd.application.pipeline_execution_history_port import PipelineExecutionHistoryPort
from acd.domain.entities.pipeline_execution import PipelineExecution


class PipelineHistoryService:
    """Application service for recording and querying IAP history."""

    def __init__(self, repository: PipelineExecutionHistoryPort, retention_limit: int = 100) -> None:
        self._repository = repository
        self._retention_limit = retention_limit

    def register_execution(
        self, execution_id: str, pipeline_id: str, pipeline_version: str, status: str, diagnostics: dict[str, Any]
    ) -> PipelineExecution:
        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_id=pipeline_id,
            pipeline_version=pipeline_version,
            status=status,
            finished_at=datetime.now(UTC),
            duration_seconds=float(diagnostics.get("total_duration_seconds", 0.0)),
            stages=json.dumps(diagnostics.get("stage_durations", {})),
            failures=json.dumps(diagnostics.get("failures", [])),
            warnings=json.dumps(diagnostics.get("warnings", [])),
            diagnostics=json.dumps(diagnostics),
            summary=json.dumps(diagnostics.get("final_result", {})),
        )
        saved = self._repository.save(execution)
        self._repository.delete_exceeding(self._retention_limit)
        return saved

    def get_execution(self, execution_id: str) -> PipelineExecution | None:
        return self._repository.get(execution_id)

    def list_history(self, limit: int = 20) -> list[PipelineExecution]:
        return self._repository.list(limit)

    def latest_execution(self) -> PipelineExecution | None:
        return self._repository.latest()

    def statistics(self) -> dict[str, int]:
        history = self._repository.list(limit=10_000)
        return {"total": len(history), "failed": sum(item.status == "failed" for item in history)}
