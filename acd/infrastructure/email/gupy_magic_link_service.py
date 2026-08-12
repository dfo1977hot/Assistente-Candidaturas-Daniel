"""Secure retrieval of short-lived Gupy passwordless login links."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from email import policy
from email.message import Message
from email.parser import BytesParser
import imaplib
import re
import time
from urllib.parse import urlparse


class MissingEmailCredentialError(RuntimeError):
    """Raised when the IMAP password has not been stored securely."""


@dataclass(frozen=True, slots=True)
class GupyMagicLinkConfig:
    host: str = "imap.terra.com.br"
    port: int = 993
    mailbox: str = "INBOX"
    timeout_seconds: int = 300
    poll_interval_seconds: int = 5


class WindowsCredentialStore:
    """Store the mail password through the operating-system keyring."""

    service_name = "ACD-Gupy-IMAP"

    def get_password(self, email_address: str) -> str | None:
        try:
            import keyring
        except ImportError as error:  # pragma: no cover - runtime dependency
            raise RuntimeError("A dependência keyring não está instalada.") from error
        return keyring.get_password(self.service_name, email_address)

    def set_password(self, email_address: str, password: str) -> None:
        try:
            import keyring
        except ImportError as error:  # pragma: no cover - runtime dependency
            raise RuntimeError("A dependência keyring não está instalada.") from error
        keyring.set_password(self.service_name, email_address, password)


class GupyMagicLinkService:
    """Poll an IMAP inbox and return only a recent, validated Gupy login link."""

    _URL_PATTERN = re.compile(r"https://[^\s<>\"']+", re.IGNORECASE)

    def __init__(
        self,
        credential_store: WindowsCredentialStore | None = None,
        config: GupyMagicLinkConfig | None = None,
    ) -> None:
        self.credential_store = credential_store or WindowsCredentialStore()
        self.config = config or GupyMagicLinkConfig()

    def has_credential(self, email_address: str) -> bool:
        return bool(self.credential_store.get_password(email_address))

    def save_credential(self, email_address: str, password: str) -> None:
        if not password:
            raise ValueError("A senha do e-mail não pode ficar vazia.")
        self.credential_store.set_password(email_address, password)

    def wait_for_link(
        self,
        *,
        email_address: str,
        requested_after: datetime,
        progress: object | None = None,
    ) -> str:
        password = self.credential_store.get_password(email_address)
        if not password:
            raise MissingEmailCredentialError(
                "A senha IMAP não está salva no Gerenciador de Credenciais do Windows."
            )
        callback = progress if callable(progress) else (lambda _value: None)
        deadline = time.monotonic() + self.config.timeout_seconds
        seen_ids: set[bytes] = set()

        with imaplib.IMAP4_SSL(self.config.host, self.config.port) as client:
            client.login(email_address, password)
            client.select(self.config.mailbox, readonly=True)
            while time.monotonic() < deadline:
                callback((62, "Aguardando o e-mail de acesso da Gupy"))
                status, data = client.search(None, "UNSEEN")
                if status != "OK":
                    status, data = client.search(None, "ALL")
                message_ids = [] if not data else data[0].split()
                for message_id in reversed(message_ids[-30:]):
                    if message_id in seen_ids:
                        continue
                    seen_ids.add(message_id)
                    status, payload = client.fetch(message_id, "(RFC822)")
                    if status != "OK" or not payload:
                        continue
                    raw = next(
                        (part[1] for part in payload if isinstance(part, tuple)),
                        None,
                    )
                    if not isinstance(raw, bytes):
                        continue
                    message = BytesParser(policy=policy.default).parsebytes(raw)
                    link = self._validated_link(message, requested_after)
                    if link:
                        callback((72, "Link de acesso recebido e validado"))
                        return link
                time.sleep(self.config.poll_interval_seconds)

        raise TimeoutError(
            "O e-mail de acesso da Gupy não chegou dentro de cinco minutos."
        )

    def _validated_link(
        self,
        message: Message,
        requested_after: datetime,
    ) -> str | None:
        sender = str(message.get("From", "")).lower()
        subject = str(message.get("Subject", "")).lower()
        if "gupy" not in sender and "gupy" not in subject:
            return None

        date_value = message.get("Date")
        if date_value:
            from email.utils import parsedate_to_datetime

            try:
                received_at = parsedate_to_datetime(str(date_value))
                if received_at.tzinfo is None:
                    received_at = received_at.replace(tzinfo=UTC)
                requested = requested_after
                if requested.tzinfo is None:
                    requested = requested.replace(tzinfo=UTC)
                if received_at < requested:
                    return None
            except (TypeError, ValueError, OverflowError):
                return None

        for body in self._message_bodies(message):
            for candidate in self._URL_PATTERN.findall(body):
                cleaned = candidate.rstrip(").,;")
                host = urlparse(cleaned).netloc.lower()
                if host == "gupy.io" or host.endswith(".gupy.io"):
                    return cleaned
        return None

    @staticmethod
    def _message_bodies(message: Message) -> tuple[str, ...]:
        bodies: list[str] = []
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() not in {"text/plain", "text/html"}:
                    continue
                try:
                    bodies.append(str(part.get_content()))
                except (LookupError, UnicodeDecodeError):
                    continue
        else:
            try:
                bodies.append(str(message.get_content()))
            except (LookupError, UnicodeDecodeError):
                ...
        return tuple(bodies)
