from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from acd.infrastructure.query_adapters.ats_history_query_adapter import ATSHistoryQueryAdapter
from acd.infrastructure.query_adapters.interview_query_adapter import InterviewQueryAdapter


class FakeATSRepository:
    """Read-only ATS repository double for adapter tests."""

    def __init__(self, history: list[object]) -> None:
        self._history = history

    def get_history(self) -> list[object]:
        return self._history


class FakeInterviewRepository:
    """Read-only interview repository double for adapter tests."""

    def __init__(self, interviews: list[object]) -> None:
        self._interviews = interviews

    def get_all(self) -> list[object]:
        return self._interviews


def test_ats_history_query_adapter_returns_latest_existing_score() -> None:
    """The adapter reads persisted history without triggering an ATS analysis."""
    now = datetime.now(UTC)
    adapter = ATSHistoryQueryAdapter(
        FakeATSRepository(
            [
                SimpleNamespace(id=2, curriculum_id=4, job_profile_id=None, total_score=82, calculated_at=now),
                SimpleNamespace(id=1, curriculum_id=3, job_profile_id=7, total_score=70, calculated_at=now),
            ]
        )
    )

    result = adapter.get_latest_for_curriculum(4)

    assert result is not None
    assert result.total_score == 82.0
    assert result.job_profile_id is None
    assert adapter.get_latest_for_curriculum(99) is None


def test_interview_query_adapter_returns_only_matching_application_dtos() -> None:
    """The adapter projects only persisted interviews for the requested application."""
    now = datetime.now(UTC)
    adapter = InterviewQueryAdapter(
        FakeInterviewRepository(
            [
                SimpleNamespace(id=1, application_id=4, interview_date=now, interview_type="Técnica", result="Agendada"),
                SimpleNamespace(id=2, application_id=5, interview_date=now, interview_type="RH", result="Agendada"),
            ]
        )
    )

    interviews = adapter.list_by_application(4)

    assert len(interviews) == 1
    assert interviews[0].interview_type == "Técnica"
    assert adapter.list_by_application(99) == ()
