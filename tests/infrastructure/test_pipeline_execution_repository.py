from __future__ import annotations

import json

from acd.application.pipeline_history_service import PipelineHistoryService
from acd.infrastructure.repositories.pipeline_execution_repository import (
    SqlAlchemyPipelineExecutionRepository,
)


def test_repository_persists_and_deserializes_execution(db_session) -> None:
    service = PipelineHistoryService(SqlAlchemyPipelineExecutionRepository())

    service.register_execution(
        "execution-1",
        "iap",
        "v1",
        "completed",
        {"stage_durations": {"ats": 0.5}, "failures": [], "warnings": [], "final_result": {"score": 90}},
    )

    execution = service.get_execution("execution-1")

    assert execution is not None
    assert json.loads(execution.stages) == {"ats": 0.5}
    assert json.loads(execution.summary) == {"score": 90}


def test_repository_applies_configurable_retention(db_session) -> None:
    service = PipelineHistoryService(SqlAlchemyPipelineExecutionRepository(), retention_limit=1)

    service.register_execution("execution-1", "iap", "v1", "completed", {})
    service.register_execution("execution-2", "iap", "v1", "failed", {})

    history = service.list_history()

    assert len(history) == 1
    assert history[0].execution_id == "execution-2"
