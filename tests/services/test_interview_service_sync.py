from __future__ import annotations

from datetime import date, datetime

from acd.domain.entities.interview import Interview
from acd.services.interview_service import InterviewService


class FakeInterviewRepository:
    def __init__(self) -> None:
        self.items: dict[int, Interview] = {}

    def create(self, interview: Interview) -> Interview:
        interview.id = len(self.items) + 1
        self.items[interview.id] = interview
        return interview

    def update(self, interview: Interview) -> Interview:
        self.items[interview.id] = interview
        return interview

    def delete(self, interview_id: int) -> bool:
        return self.items.pop(interview_id, None) is not None

    def get_by_id(self, interview_id: int) -> Interview | None:
        return self.items.get(interview_id)

    def get_for_application(self, application_id: int) -> list[Interview]:
        return sorted(
            (item for item in self.items.values() if item.application_id == application_id),
            key=lambda item: item.interview_date,
        )


class FakeApplicationRepository:
    def __init__(self) -> None:
        self.events: list[tuple[int, str, str]] = []

    def add_event(self, application_id: int, event_type: str, description: str) -> None:
        self.events.append((application_id, event_type, description))


class FakeApplicationService:
    def __init__(self) -> None:
        self.repository = FakeApplicationRepository()
        self.synced: list[tuple[int, date | None]] = []

    def set_interview_date(self, application_id: int, interview_date: date | None):
        self.synced.append((application_id, interview_date))
        return object()


def create_service() -> tuple[InterviewService, FakeInterviewRepository, FakeApplicationService]:
    repository = FakeInterviewRepository()
    application_service = FakeApplicationService()
    service = InterviewService(
        repository=repository,
        application_service=application_service,  # type: ignore[arg-type]
    )
    return service, repository, application_service


def test_create_interview_updates_application_date() -> None:
    service, _, application_service = create_service()

    service.create_interview(
        application_id=10,
        interview_date=datetime(2026, 9, 12, 14, 30),
        interview_type="RH",
    )

    assert application_service.synced[-1] == (10, date(2026, 9, 12))


def test_update_interview_recalculates_previous_and_current_application() -> None:
    service, _, application_service = create_service()
    interview = service.create_interview(
        application_id=10,
        interview_date=datetime(2026, 9, 12, 14, 30),
        interview_type="RH",
    )
    application_service.synced.clear()

    service.update_interview(
        interview.id,
        application_id=11,
        interview_date=datetime(2026, 9, 20, 10, 0),
        interview_type="Gestor",
    )

    assert application_service.synced == [
        (10, None),
        (11, date(2026, 9, 20)),
    ]


def test_delete_last_interview_clears_application_date() -> None:
    service, _, application_service = create_service()
    interview = service.create_interview(
        application_id=10,
        interview_date=datetime(2026, 9, 12, 14, 30),
        interview_type="RH",
    )
    application_service.synced.clear()

    assert service.delete_interview(interview.id) is True
    assert application_service.synced == [(10, None)]
