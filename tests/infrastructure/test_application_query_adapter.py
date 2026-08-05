from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from acd.infrastructure.query_adapters.application_query_adapter import ApplicationQueryAdapter


class FakeApplicationRepository:
    """Read-only repository double for adapter tests."""

    def __init__(self, application: object | None, history: list[object]) -> None:
        self._application = application
        self._history = history

    def get_by_id(self, application_id: int) -> object | None:
        return self._application

    def get_followups(self, application_id: int) -> list[object]:
        return self._history


def test_application_query_adapter_maps_application_and_history() -> None:
    """Repository entities are exposed only through Application DTOs."""
    application = SimpleNamespace(
        id=1,
        job_id=2,
        company_id=3,
        curriculum_id=4,
        curriculum_version="v1.0",
        status="Aplicada",
    )
    history = [
        SimpleNamespace(
            event_type="created",
            description="Candidatura criada",
            created_at=datetime.now(UTC),
        )
    ]
    adapter = ApplicationQueryAdapter(FakeApplicationRepository(application, history))

    result = adapter.get_by_id(1)

    assert result is not None
    assert result.status == "Aplicada"
    assert adapter.list_history(1)[0].event_type == "created"


def test_application_query_adapter_returns_none_for_unknown_application() -> None:
    """Missing repository entities remain absent from the query contract."""
    adapter = ApplicationQueryAdapter(FakeApplicationRepository(None, []))

    assert adapter.get_by_id(999) is None
