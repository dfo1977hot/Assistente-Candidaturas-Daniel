from __future__ import annotations

from typing import Protocol

from acd.domain.entities.pipeline_execution import PipelineExecution


class PipelineExecutionHistoryPort(Protocol):
    """Persistence contract for IAP execution history."""

    def save(self, execution: PipelineExecution) -> PipelineExecution: ...

    def get(self, execution_id: str) -> PipelineExecution | None: ...

    def list(self, limit: int = 20) -> list[PipelineExecution]: ...

    def latest(self) -> PipelineExecution | None: ...

    def delete_exceeding(self, maximum_records: int) -> int: ...
