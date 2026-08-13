from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace

import pytest

from acd.infrastructure.email.classic_outlook_mail_reader import (
    ClassicOutlookMailReader,
    OutlookClassicUnavailableError,
)


class Items:
    def __init__(self, values: list[object]) -> None:
        self.values = values
        self.Count = len(values)
        self.sorted = False

    def Sort(self, field: str, descending: bool) -> None:
        assert field == "[ReceivedTime]"
        assert descending is True
        self.values.sort(key=lambda item: item.ReceivedTime, reverse=True)
        self.sorted = True

    def Item(self, index: int) -> object:
        return self.values[index - 1]


def reader_for(values: list[object]):
    items = Items(values)
    inbox = SimpleNamespace(Items=items)
    namespace = SimpleNamespace(GetDefaultFolder=lambda folder: inbox)

    class Outlook:
        def GetNamespace(self, name: str):
            assert name == "MAPI"
            return namespace

    lifecycle: list[str] = []
    reader = ClassicOutlookMailReader(
        dispatch=lambda prog_id: Outlook(),
        co_initialize=lambda: lifecycle.append("init"),
        co_uninitialize=lambda: lifecycle.append("uninit"),
    )
    return reader, items, lifecycle


def mail(
    *,
    entry_id: str = "entry-1",
    sender: str = "recrutador@example.com",
    received: datetime = datetime(2026, 8, 13, 9, 30),
    subject: str = "Retorno",
) -> object:
    return SimpleNamespace(
        Class=43,
        EntryID=entry_id,
        SenderEmailType="SMTP",
        SenderEmailAddress=sender,
        ReceivedTime=received,
        Subject=subject,
    )


def test_reads_exact_sender_from_default_inbox_and_initializes_com() -> None:
    reader, items, lifecycle = reader_for(
        [mail(sender="outro@example.com"), mail(entry_id="entry-2")]
    )
    result = reader.read_from_sender("recrutador@example.com", since=date(2026, 8, 1))
    assert items.sorted is True
    assert lifecycle == ["init", "uninit"]
    assert [item.message_id for item in result] == ["entry-2"]
    assert result[0].source == "outlook_classic"


def test_stops_after_messages_older_than_since() -> None:
    reader, _, _ = reader_for([
        mail(entry_id="new", received=datetime(2026, 8, 13, 9, 0)),
        mail(entry_id="old", received=datetime(2026, 7, 30, 9, 0)),
    ])
    result = reader.read_from_sender("recrutador@example.com", since=date(2026, 8, 1))
    assert [item.message_id for item in result] == ["new"]


def test_resolves_exchange_sender_primary_smtp_address() -> None:
    exchange_user = SimpleNamespace(PrimarySmtpAddress="recrutador@example.com")
    sender = SimpleNamespace(GetExchangeUser=lambda: exchange_user)
    item = mail()
    item.SenderEmailType = "EX"
    item.Sender = sender
    item.SenderEmailAddress = "/O=EXAMPLE/OU=EXCHANGE/CN=RECIPIENTS/CN=ABC"
    reader, _, _ = reader_for([item])
    result = reader.read_from_sender("recrutador@example.com")
    assert len(result) == 1
    assert result[0].sender_email == "recrutador@example.com"


def test_com_is_uninitialized_when_outlook_access_fails() -> None:
    lifecycle: list[str] = []
    reader = ClassicOutlookMailReader(
        dispatch=lambda _prog_id: (_ for _ in ()).throw(RuntimeError("COM failure")),
        co_initialize=lambda: lifecycle.append("init"),
        co_uninitialize=lambda: lifecycle.append("uninit"),
    )
    with pytest.raises(OutlookClassicUnavailableError, match="Outlook Classic"):
        reader.read_from_sender("recrutador@example.com")
    assert lifecycle == ["init", "uninit"]


def test_non_positive_limit_does_not_touch_com() -> None:
    reader = ClassicOutlookMailReader(
        dispatch=lambda _prog_id: pytest.fail("COM não deveria ser chamado"),
        co_initialize=lambda: pytest.fail("COM não deveria ser inicializado"),
        co_uninitialize=lambda: pytest.fail("COM não deveria ser finalizado"),
    )
    assert reader.read_from_sender("recrutador@example.com", limit=0) == ()
