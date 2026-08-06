from __future__ import annotations

from typing import Any

from acd.application.pipeline_history_service import PipelineHistoryService


def register_pipeline_execution(service: PipelineHistoryService, **kwargs: Any) -> object:
    return service.register_execution(**kwargs)


def get_pipeline_execution(service: PipelineHistoryService, execution_id: str) -> object:
    return service.get_execution(execution_id)


def list_pipeline_history(service: PipelineHistoryService, limit: int = 20) -> object:
    return service.list_history(limit)


def get_latest_pipeline_execution(service: PipelineHistoryService) -> object:
    return service.latest_execution()


def get_pipeline_statistics(service: PipelineHistoryService) -> dict[str, int]:
    return service.statistics()
