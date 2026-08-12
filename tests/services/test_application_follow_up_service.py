from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from acd.services.application_follow_up_service import ApplicationFollowUpService
from acd.services.workflow_step_registry import ProductiveWorkflowHandlers


class FollowUpRepositoryStub:
    def __init__(self, application: SimpleNamespace) -> None:
        self.application = application
        self.events: list[SimpleNamespace] = []

    def get_by_id(self, application_id: int):
        return self.application if application_id == self.application.id else None

    def get_all(self):
        return [self.application]

    def update(self, application):
        self.application = application
        return application

    def get_followups(self, application_id: int):
        assert application_id == self.application.id
        return sorted(self.events, key=lambda item: (item.created_at, item.id))

    def add_event(self, application_id, event_type, description, **metadata):
        event = SimpleNamespace(
            id=len(self.events) + 1,
            application_id=application_id,
            event_type=event_type,
            description=description,
            created_at=metadata.pop("created_at", datetime.now()),
            origin=metadata.pop("origin", "manual"),
            reference_type=metadata.pop("reference_type", ""),
            reference_id=metadata.pop("reference_id", None),
        )
        self.events.append(event)
        return event


@pytest.fixture
def follow_up():
    today = date(2026, 8, 12)
    application = SimpleNamespace(
        id=7,
        status="Aplicada",
        next_action="",
        next_follow_up=None,
        follow_up_time="",
        follow_up_priority="Normal",
        follow_up_note="",
        response_date=None,
        interview_date=None,
        last_update=today,
        updated_at=datetime(2026, 8, 12, 9),
    )
    repository = FollowUpRepositoryStub(application)
    return ApplicationFollowUpService(repository), repository, today


def test_create_future_action_preserves_priority_without_false_attention(follow_up):
    service, _, today = follow_up
    state = service.set_next_action(
        7,
        action="Enviar follow-up",
        follow_up_date=today + timedelta(days=2),
        follow_up_time="09:30",
        priority="Alta",
        note="Revisar o contato informado",
    )
    assert state.priority == "Alta"
    assert state.follow_up_date == today + timedelta(days=2)
    assert service.is_overdue(7, today=today) is False


def test_overdue_complete_and_postpone_follow_up(follow_up):
    service, _, today = follow_up
    service.set_next_action(
        7, action="Verificar status", follow_up_date=today - timedelta(days=1)
    )
    assert service.is_overdue(7, today=today) is True
    postponed = service.postpone_follow_up(7, today + timedelta(days=3))
    assert postponed.follow_up_date == today + timedelta(days=3)
    completed = service.complete_follow_up(7)
    assert completed.next_action == ""
    assert completed.follow_up_date is None


def test_timeline_is_chronological_and_does_not_invent_events(follow_up):
    service, repository, _ = follow_up
    assert service.get_timeline(7) == ()
    service.register_interaction(
        7,
        interaction_type="E-mail enviado",
        summary="Mensagem enviada manualmente ao contato já registrado",
        occurred_at=datetime(2026, 8, 12, 14),
    )
    service.register_interaction(
        7,
        interaction_type="Candidatura enviada",
        summary="Envio confirmado pelo usuário",
        occurred_at=datetime(2026, 8, 11, 10),
    )
    timeline = service.get_timeline(7)
    assert [item.interaction_type for item in timeline] == [
        "Candidatura enviada",
        "E-mail enviado",
    ]
    assert repository.application.response_date is None


@pytest.mark.parametrize(
    "interaction_type", ["Retorno recebido", "Feedback recebido", "Proposta recebida", "Rejeição"]
)
def test_only_real_response_interaction_sets_response_date(follow_up, interaction_type):
    service, repository, _ = follow_up
    service.register_interaction(
        7,
        interaction_type=interaction_type,
        summary="Evento real confirmado manualmente",
        occurred_at=datetime(2026, 8, 13, 11, 30),
    )
    assert repository.application.response_date == date(2026, 8, 13)


def test_stale_application_and_upcoming_interview_require_attention(follow_up):
    service, repository, today = follow_up
    repository.application.last_update = today - timedelta(days=15)
    repository.application.interview_date = today + timedelta(days=2)
    state = service.get_state(7, today=today)
    assert state.attention_reasons == ("stale_application", "upcoming_interview")


def test_letter_use_is_manual_and_referenced(follow_up):
    service, _, _ = follow_up
    item = service.register_letter_usage(7, 42)
    assert item.reference_type == "cover_letter"
    assert item.reference_id == 42


def test_workflow_handlers_use_real_follow_up_service(follow_up):
    service, _, today = follow_up
    handlers = object.__new__(ProductiveWorkflowHandlers)
    handlers.application_follow_up_service = service
    review = handlers.review_application({}, {"application_id": 7})
    assert review["status"] == "Concluída"
    assert review["context_updates"]["follow_up_required"] is False

    service.set_next_action(
        7, action="Enviar follow-up", follow_up_date=today - timedelta(days=1)
    )
    check = handlers.check_follow_up({}, {"application_id": 7})
    assert check["status"] == "Aguardando usuário"


def test_workflow_without_overdue_follow_up_creates_no_action(follow_up):
    service, repository, _ = follow_up
    handlers = object.__new__(ProductiveWorkflowHandlers)
    handlers.application_follow_up_service = service
    result = handlers.check_follow_up({}, {"application_id": 7})
    assert result["status"] == "Concluída"
    assert repository.application.next_action == ""


def test_invalid_time_and_missing_real_summary_are_rejected(follow_up):
    service, _, today = follow_up
    with pytest.raises(ValueError, match="HH:MM"):
        service.set_next_action(
            7,
            action="Enviar follow-up",
            follow_up_date=today,
            follow_up_time="25:10",
        )
    with pytest.raises(ValueError, match="resumo"):
        service.register_interaction(7, interaction_type="Retorno recebido", summary=" ")
