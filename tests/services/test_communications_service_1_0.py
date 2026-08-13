from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from acd.services.communications_service import CommunicationsService, MailMessage


@dataclass
class TimelineItem:
    reference_type: str = ""
    reference_id: int | None = None


class ApplicationServiceStub:
    def __init__(self, application: object | None) -> None:
        self.application = application

    def get_application(self, application_id: int) -> object | None:
        application = self.application
        if application is None or getattr(application, "id", None) != application_id:
            return None
        return application


class FollowUpServiceStub:
    def __init__(self) -> None:
        self.timeline: list[TimelineItem] = []
        self.calls: list[dict[str, object]] = []

    def get_timeline(self, application_id: int) -> tuple[TimelineItem, ...]:
        del application_id
        return tuple(self.timeline)

    def register_interaction(self, application_id: int, **data: object) -> object:
        self.calls.append({"application_id": application_id, **data})
        item = TimelineItem(
            reference_type=str(data.get("reference_type", "")),
            reference_id=int(data["reference_id"]) if data.get("reference_id") is not None else None,
        )
        self.timeline.append(item)
        return item


class MailReaderStub:
    def __init__(self, messages: tuple[MailMessage, ...]) -> None:
        self.messages = messages
        self.calls: list[tuple[str, date | None, int]] = []

    def read_from_sender(
        self,
        sender_email: str,
        *,
        since: date | None = None,
        limit: int = 50,
    ) -> tuple[MailMessage, ...]:
        self.calls.append((sender_email, since, limit))
        return self.messages


def application(**overrides: object) -> object:
    values: dict[str, object] = {
        "id": 1,
        "recruiter_email": "recrutador@example.com",
        "application_date": date(2026, 8, 1),
        "created_at": datetime(2026, 8, 1, 10, 0),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def message(
    message_id: str = "<abc@example.com>",
    *,
    sender: str = "recrutador@example.com",
    subject: str = "Retorno sobre a vaga",
    source: str = "outlook_classic",
) -> MailMessage:
    return MailMessage(
        message_id=message_id,
        sender_email=sender,
        subject=subject,
        received_at=datetime(2026, 8, 13, 9, 30),
        source=source,
    )


def test_sync_registers_real_incoming_email_as_response() -> None:
    follow_up = FollowUpServiceStub()
    reader = MailReaderStub((message(),))
    service = CommunicationsService(ApplicationServiceStub(application()), follow_up, reader)

    result = service.sync_application(1)

    assert result.imported_messages == 1
    assert result.skipped_duplicates == 0
    assert reader.calls == [("recrutador@example.com", date(2026, 8, 1), 50)]
    assert follow_up.calls[0]["interaction_type"] == "Retorno recebido"
    assert follow_up.calls[0]["origin"] == "outlook_classic"
    assert follow_up.calls[0]["reference_type"] == "mail_message"
    assert "Retorno sobre a vaga" in str(follow_up.calls[0]["summary"])


def test_sync_is_idempotent_for_same_provider_message() -> None:
    follow_up = FollowUpServiceStub()
    reader = MailReaderStub((message(),))
    service = CommunicationsService(ApplicationServiceStub(application()), follow_up, reader)

    first = service.sync_application(1)
    second = service.sync_application(1)

    assert first.imported_messages == 1
    assert second.imported_messages == 0
    assert second.skipped_duplicates == 1
    assert len(follow_up.calls) == 1


def test_same_message_id_from_different_provider_has_distinct_identity() -> None:
    first = CommunicationsService._message_reference_id(message(source="outlook_classic"))
    second = CommunicationsService._message_reference_id(message(source="other_provider"))

    assert first != second


def test_sync_ignores_message_whose_sender_does_not_exactly_match() -> None:
    follow_up = FollowUpServiceStub()
    reader = MailReaderStub((message(sender="outro@example.com"),))
    service = CommunicationsService(ApplicationServiceStub(application()), follow_up, reader)

    result = service.sync_application(1)

    assert result.imported_messages == 0
    assert follow_up.calls == []


def test_sync_requires_recruiter_email() -> None:
    service = CommunicationsService(
        ApplicationServiceStub(application(recruiter_email="")),
        FollowUpServiceStub(),
        MailReaderStub(()),
    )

    with pytest.raises(ValueError, match="e-mail do recrutador"):
        service.sync_application(1)


def test_sync_reports_provider_neutral_progress() -> None:
    service = CommunicationsService(
        ApplicationServiceStub(application()),
        FollowUpServiceStub(),
        MailReaderStub((message(),)),
    )
    progress: list[tuple[int, str]] = []

    service.sync_application(1, progress=progress.append)

    assert progress[0] == (10, "Consultando e-mails...")
    assert progress[-1] == (100, "Sincronização de comunicações concluída.")
