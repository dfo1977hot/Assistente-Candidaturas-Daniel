from __future__ import annotations

from acd.application.pipeline_history_service import PipelineHistoryService


class FakeRepository:
    def __init__(self) -> None:
        self.items = []

    def save(self, execution):
        self.items.append(execution)
        return execution

    def get(self, execution_id: str):
        return next((item for item in self.items if item.execution_id == execution_id), None)

    def list(self, limit: int = 20):
        return self.items[:limit]

    def latest(self):
        return self.items[0] if self.items else None

    def delete_exceeding(self, maximum_records: int):
        del self.items[maximum_records:]
        return 0


def test_history_service_serializes_and_queries_execution() -> None:
    service = PipelineHistoryService(FakeRepository())

    execution = service.register_execution(
        "execution-1", "iap", "v1", "completed", {"failures": [], "final_result": {"score": 90}}
    )

    assert service.get_execution("execution-1") is execution
    assert service.latest_execution() is execution
    assert service.statistics() == {"total": 1, "failed": 0}
