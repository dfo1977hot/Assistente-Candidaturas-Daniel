from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
import hashlib
from typing import Protocol


@dataclass(frozen=True, slots=True)
class MailMessage:
    """Provider-neutral representation of one incoming e-mail."""

    message_id: str
    sender_email: str
    subject: str
    received_at: datetime
    source: str = "mail"


@dataclass(frozen=True, slots=True)
class CommunicationsSyncResult:
    application_id: int
    matched_messages: int
    imported_messages: int
    skipped_duplicates: int


class MailMessageReader(Protocol):
    """Boundary implemented by concrete mail providers."""

    def read_from_sender(
        self,
        sender_email: str,
        *,
        since: date | None = None,
        limit: int = 50,
    ) -> tuple[MailMessage, ...]: ...


class ApplicationLookup(Protocol):
    def get_application(self, application_id: int) -> object | None: ...


class FollowUpTimeline(Protocol):
    def get_timeline(self, application_id: int) -> tuple[object, ...]: ...

    def register_interaction(self, application_id: int, **data: object) -> object: ...


class CommunicationsService:
    """Import incoming recruiter e-mails into the application timeline.

    Provider-specific authentication and mailbox access stay behind
    ``MailMessageReader``. This service never sends, replies to, deletes,
    moves, labels, or marks e-mails as read.
    """

    def __init__(
        self,
        application_service: ApplicationLookup,
        follow_up_service: FollowUpTimeline,
        mail_reader: MailMessageReader,
    ) -> None:
        self._application_service = application_service
        self._follow_up_service = follow_up_service
        self._mail_reader = mail_reader

    def sync_application(
        self,
        application_id: int,
        *,
        progress: Callable[[tuple[int, str]], None] | None = None,
    ) -> CommunicationsSyncResult:
        application = self._application_service.get_application(application_id)
        if application is None:
            raise ValueError("Candidatura não encontrada.")

        recruiter_email = str(getattr(application, "recruiter_email", "") or "").strip()
        if not recruiter_email:
            raise ValueError(
                "Informe o e-mail do recrutador antes de sincronizar as comunicações."
            )

        if progress is not None:
            progress((10, "Consultando e-mails..."))

        since = self._start_date(application)
        messages = self._mail_reader.read_from_sender(recruiter_email, since=since)
        existing_ids = self._existing_reference_ids(application_id)

        if progress is not None:
            progress((45, f"{len(messages)} mensagem(ns) encontrada(s)."))

        imported = 0
        skipped = 0
        for index, message in enumerate(messages, start=1):
            if message.sender_email.casefold() != recruiter_email.casefold():
                continue
            reference_id = self._message_reference_id(message)
            if reference_id in existing_ids:
                skipped += 1
                continue
            self._follow_up_service.register_interaction(
                application_id,
                interaction_type="Retorno recebido",
                summary=self._summary(message),
                occurred_at=message.received_at,
                origin=message.source.strip() or "mail",
                reference_type="mail_message",
                reference_id=reference_id,
            )
            existing_ids.add(reference_id)
            imported += 1
            if progress is not None:
                value = 45 + int((index / max(len(messages), 1)) * 50)
                progress((min(value, 95), "Registrando respostas na timeline..."))

        if progress is not None:
            progress((100, "Sincronização de comunicações concluída."))

        return CommunicationsSyncResult(
            application_id=application_id,
            matched_messages=len(messages),
            imported_messages=imported,
            skipped_duplicates=skipped,
        )

    def _existing_reference_ids(self, application_id: int) -> set[int]:
        return {
            int(item.reference_id)
            for item in self._follow_up_service.get_timeline(application_id)
            if getattr(item, "reference_type", "") == "mail_message"
            and getattr(item, "reference_id", None) is not None
        }

    @staticmethod
    def _start_date(application: object) -> date | None:
        application_date = getattr(application, "application_date", None)
        if isinstance(application_date, date):
            return application_date
        created_at = getattr(application, "created_at", None)
        if isinstance(created_at, datetime):
            return created_at.date()
        return None

    @staticmethod
    def _message_reference_id(message: MailMessage) -> int:
        identity = message.message_id.strip() or (
            f"{message.sender_email}|{message.received_at.isoformat()}|{message.subject}"
        )
        provider_identity = f"{message.source.casefold()}|{identity}"
        digest = hashlib.blake2b(provider_identity.encode(), digest_size=8).digest()
        return int.from_bytes(digest, "big") & ((1 << 63) - 1)

    @staticmethod
    def _summary(message: MailMessage) -> str:
        subject = message.subject.strip() or "(sem assunto)"
        return f"E-mail recebido de {message.sender_email}: {subject}"
