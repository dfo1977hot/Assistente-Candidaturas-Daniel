from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from acd.services.application_follow_up_service import ApplicationFollowUpService


@dataclass
class Event:
    id: int
    application_id: int
    event_type: str
    description: str
    origin: str = "manual"
    reference_type: str = ""
    reference_id: int | None = None
    created_at: datetime = datetime(2026, 8, 12, 12, 0)


class RepositoryStub:
    def __init__(self, application):
        self.application = application
        self.events: list[Event] = []
        self._next_id = 1

    def get_by_id(self, application_id: int):
        return self.application if self.application.id == application_id else None

    def get_all(self):
        return [self.application]

    def update(self, application):
        self.application = application
        return application

    def get_followups(self, application_id: int):
        return [item for item in self.events if item.application_id == application_id]

    def add_event(self, application_id, event_type, description, **metadata):
        event = Event(
            id=self._next_id,
            application_id=application_id,
            event_type=event_type,
            description=description,
            origin=str(metadata.get("origin", "manual")),
            reference_type=str(metadata.get("reference_type", "")),
            reference_id=metadata.get("reference_id"),
            created_at=metadata.get("created_at") or datetime(2026, 8, 12, 12, 0),
        )
        self._next_id += 1
        self.events.append(event)
        return event


def application(**overrides):
    values = {
        "id": 1,
        "status": "Aplicada",
        "next_action": "",
        "next_follow_up": None,
        "follow_up_time": "",
        "follow_up_priority": "Normal",
        "follow_up_note": "",
        "last_update": date(2026, 8, 12),
        "updated_at": datetime(2026, 8, 12, 10, 0),
        "response_date": None,
        "interview_date": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_next_action_and_priority_are_persisted() -> None:
    repository = RepositoryStub(application())
    service = ApplicationFollowUpService(repository)

    state = service.set_next_action(
        1,
        action="Enviar follow-up",
        follow_up_date=date(2026, 8, 15),
        follow_up_time="09:30",
        priority="Alta",
        note="Cobrar retorno do recrutador.",
    )

    assert state.next_action == "Enviar follow-up"
    assert state.follow_up_date == date(2026, 8, 15)
    assert state.follow_up_time == "09:30"
    assert state.priority == "Alta"
    assert state.note == "Cobrar retorno do recrutador."


def test_overdue_follow_up_requires_attention() -> None:
    repository = RepositoryStub(
        application(
            next_action="Verificar status",
            next_follow_up=date(2026, 8, 10),
        )
    )
    service = ApplicationFollowUpService(repository)

    state = service.get_state(1, today=date(2026, 8, 12))

    assert state.follow_up_required is True
    assert "follow_up_overdue" in state.attention_reasons


def test_future_follow_up_is_not_overdue() -> None:
    repository = RepositoryStub(
        application(
            next_action="Verificar status",
            next_follow_up=date(2026, 8, 20),
        )
    )
    service = ApplicationFollowUpService(repository)

    assert service.is_overdue(1, today=date(2026, 8, 12)) is False


def test_complete_follow_up_clears_schedule_without_fake_response() -> None:
    row = application(
        next_action="Enviar follow-up",
        next_follow_up=date(2026, 8, 10),
        follow_up_time="09:00",
        response_date=None,
    )
    repository = RepositoryStub(row)
    service = ApplicationFollowUpService(repository)

    state = service.complete_follow_up(1)

    assert state.next_action == ""
    assert state.follow_up_date is None
    assert repository.application.response_date is None


def test_postpone_follow_up_keeps_action_and_changes_date() -> None:
    repository = RepositoryStub(
        application(
            next_action="Enviar follow-up",
            next_follow_up=date(2026, 8, 10),
        )
    )
    service = ApplicationFollowUpService(repository)

    state = service.postpone_follow_up(1, date(2026, 8, 18))

    assert state.next_action == "Enviar follow-up"
    assert state.follow_up_date == date(2026, 8, 18)


def test_real_response_interaction_is_the_only_path_that_sets_response_date() -> None:
    repository = RepositoryStub(application(response_date=None))
    service = ApplicationFollowUpService(repository)

    service.register_interaction(
        1,
        interaction_type="E-mail enviado",
        summary="Follow-up enviado.",
        occurred_at=datetime(2026, 8, 12, 10, 0),
    )
    assert repository.application.response_date is None

    service.register_interaction(
        1,
        interaction_type="Retorno recebido",
        summary="Recrutador confirmou recebimento.",
        occurred_at=datetime(2026, 8, 13, 11, 0),
    )
    assert repository.application.response_date == date(2026, 8, 13)


def test_timeline_is_chronological_and_preserves_references() -> None:
    repository = RepositoryStub(application())
    service = ApplicationFollowUpService(repository)
    service.register_interaction(
        1,
        interaction_type="Outro",
        summary="Carta utilizada na candidatura.",
        occurred_at=datetime(2026, 8, 13, 9, 0),
        reference_type="cover_letter",
        reference_id=7,
    )
    service.register_interaction(
        1,
        interaction_type="Candidatura enviada",
        summary="Candidatura concluída.",
        occurred_at=datetime(2026, 8, 12, 9, 0),
    )

    timeline = service.get_timeline(1)

    assert [item.occurred_at.date() for item in timeline] == [
        date(2026, 8, 12),
        date(2026, 8, 13),
    ]
    assert timeline[-1].reference_type == "cover_letter"
    assert timeline[-1].reference_id == 7


def test_stale_application_without_updated_at_does_not_crash() -> None:
    row = application(last_update=None, updated_at=None)
    repository = RepositoryStub(row)
    service = ApplicationFollowUpService(repository)

    state = service.get_state(1, today=date(2026, 8, 12))

    assert "stale_application" not in state.attention_reasons


@pytest.mark.parametrize("value", ["9:00", "24:00", "09:60", "texto"])
def test_invalid_follow_up_time_is_rejected(value: str) -> None:
    repository = RepositoryStub(application())
    service = ApplicationFollowUpService(repository)

    with pytest.raises(ValueError, match="HH:MM"):
        service.set_next_action(
            1,
            action="Verificar status",
            follow_up_date=date(2026, 8, 15),
            follow_up_time=value,
        )
