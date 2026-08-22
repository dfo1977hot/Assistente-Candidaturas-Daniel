"""Read Gupy passwordless links directly from the configured Terra IMAP mailbox."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
import imaplib
import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

from acd.services.settings_service import LoginCredential, SettingsService


class TerraImapGupyMagicLinkUnavailableError(RuntimeError):
    """Raised when the configured Terra IMAP mailbox cannot be queried."""


class _AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.casefold() != "a":
            return
        href = next(
            (
                value
                for name, value in attrs
                if name.casefold() == "href" and value
            ),
            None,
        )
        if href:
            self._href = href
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() != "a" or self._href is None:
            return
        text = " ".join(part.strip() for part in self._text if part.strip())
        self.anchors.append((self._href, text))
        self._href = None
        self._text = []


class TerraImapGupyMagicLinkService:
    """Locate the newest Gupy magic link using the IMAP settings from the vault."""

    SERVICE_NAME = "Terra IMAP"
    EXPECTED_SENDER = "no-reply@gupy.com.br"

    def __init__(
        self,
        settings_service: SettingsService,
        *,
        timeout_seconds: int = 60,
        poll_interval_seconds: int = 3,
    ) -> None:
        self.settings_service = settings_service
        self._timeout_seconds = timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds

    def has_credential(self, _email_address: str) -> bool:
        configured = self.settings_service.get_imap_login(self.SERVICE_NAME)
        if configured is None:
            return False
        credential, password = configured
        return bool(
            credential.server.strip()
            and credential.username.strip()
            and credential.folder.strip()
            and password
        )

    def save_credential(self, email_address: str, password: str) -> None:
        credential = self.settings_service.get_login(self.SERVICE_NAME)
        if credential is None:
            credential = LoginCredential(
                service=self.SERVICE_NAME,
                username=email_address.strip(),
                timeout_seconds=60,
            )
        elif email_address.strip() and not credential.username.strip():
            credential.username = email_address.strip()

        self.settings_service.save_login(credential, password)



    def capture_sender_uid_baseline(
        self,
        *,
        progress: object | None = None,
    ) -> int:
        """Capture the highest current UID from the Gupy sender."""
        callback = (
            progress
            if callable(progress)
            else (lambda _value: None)
        )

        configured = self.settings_service.get_imap_login(
            self.SERVICE_NAME
        )
        if configured is None:
            raise TerraImapGupyMagicLinkUnavailableError(
                "Configure Terra IMAP no Cofre de Logins."
            )

        credential, password = configured
        self._validate_configuration(
            credential,
            password,
        )

        client = self._connect(credential)

        try:
            status, _ = client.login(
                credential.username.strip(),
                password,
            )
            if status != "OK":
                raise TerraImapGupyMagicLinkUnavailableError(
                    "O servidor IMAP recusou a autenticação."
                )

            mailbox = credential.folder.strip()
            if mailbox.casefold() == "inbox":
                mailbox = "INBOX"

            status, _ = client.select(
                mailbox,
                readonly=True,
            )
            if status != "OK":
                raise TerraImapGupyMagicLinkUnavailableError(
                    "A pasta IMAP configurada não pôde ser aberta: "
                    + credential.folder
                )

            uid = getattr(client, "uid", None)
            if not callable(uid):
                callback(
                    (
                        61,
                        "Servidor IMAP sem suporte ao baseline UID.",
                    )
                )
                return 0

            status, data = uid(
                "search",
                None,
                "FROM",
                f'"{self.EXPECTED_SENDER}"',
            )

            if status != "OK" or not data or not data[0]:
                baseline = 0
            else:
                baseline = max(
                    (
                        int(value)
                        for value in data[0].split()
                    ),
                    default=0,
                )

            callback(
                (
                    61,
                    "Baseline IMAP da Gupy capturado "
                    f"no UID {baseline}.",
                )
            )
            return baseline

        except (imaplib.IMAP4.error, OSError) as exc:
            raise TerraImapGupyMagicLinkUnavailableError(
                "Não foi possível consultar "
                "o servidor IMAP configurado."
            ) from exc

        finally:
            try:
                client.logout()
            except Exception as exc:
                logging.getLogger(__name__).debug("Falha ao encerrar a sessão IMAP: %s", exc)

    def wait_for_link(
        self,
        *,
        email_address: str,
        requested_after: datetime,
        min_uid: int | None = None,
        progress: object | None = None,
    ) -> str:
        del email_address

        callback = (
            progress
            if callable(progress)
            else (lambda _value: None)
        )

        configured = self.settings_service.get_imap_login(
            self.SERVICE_NAME
        )
        if configured is None:
            raise TerraImapGupyMagicLinkUnavailableError(
                "Configure Terra IMAP no Cofre de Logins."
            )

        credential, password = configured
        self._validate_configuration(
            credential,
            password,
        )

        timeout = max(
            int(
                self._timeout_seconds
                or credential.timeout_seconds
            ),
            1,
        )
        deadline = time.monotonic() + timeout
        requested_floor = self._normalize_requested_after(
            requested_after
        )

        while time.monotonic() < deadline:
            callback(
                (
                    63,
                    "Consultando IMAP diretamente "
                    "na pasta configurada: "
                    f"{credential.folder}",
                )
            )

            try:
                link = self._find_link_once(
                    credential,
                    password,
                    requested_floor=requested_floor,
                    progress=callback,
                    min_uid=min_uid,
                )
            except (imaplib.IMAP4.error, OSError) as exc:
                raise TerraImapGupyMagicLinkUnavailableError(
                    "Não foi possível consultar "
                    "o servidor IMAP configurado."
                ) from exc

            if link:
                return link

            time.sleep(
                self._poll_interval_seconds
            )

        raise TimeoutError(
            "O e-mail de acesso da Gupy não foi localizado "
            "na pasta IMAP configurada "
            f"({credential.folder}) dentro de "
            f"{timeout // 60 or 1} minuto(s)."
        )



    def _find_link_once(
        self,
        credential: LoginCredential,
        password: str,
        *,
        requested_floor: datetime,
        progress: Callable[[object], None],
        min_uid: int | None = None,
    ) -> str | None:
        client = self._connect(credential)

        try:
            status, _ = client.login(
                credential.username.strip(),
                password,
            )
            if status != "OK":
                raise TerraImapGupyMagicLinkUnavailableError(
                    "O servidor IMAP recusou a autenticação."
                )

            mailbox = credential.folder.strip()
            if mailbox.casefold() == "inbox":
                mailbox = "INBOX"

            status, _ = client.select(
                mailbox,
                readonly=True,
            )
            if status != "OK":
                raise TerraImapGupyMagicLinkUnavailableError(
                    "A pasta IMAP configurada não pôde ser aberta: "
                    + credential.folder
                )

            uid = getattr(client, "uid", None)
            uid_mode = callable(uid)

            if uid_mode:
                status, data = uid(
                    "search",
                    None,
                    "FROM",
                    f'"{self.EXPECTED_SENDER}"',
                )
            else:
                status, data = client.search(
                    None,
                    "FROM",
                    f'"{self.EXPECTED_SENDER}"',
                )

            if (
                status != "OK"
                or not data
                or not data[0]
            ):
                return None

            message_ids = data[0].split()

            for message_id in reversed(
                message_ids[-20:]
            ):
                try:
                    numeric_id = int(message_id)
                except (TypeError, ValueError):
                    numeric_id = 0

                if (
                    uid_mode
                    and min_uid is not None
                    and numeric_id <= min_uid
                ):
                    continue

                if uid_mode:
                    status, rows = uid(
                        "fetch",
                        message_id,
                        "(RFC822)",
                    )
                else:
                    status, rows = client.fetch(
                        message_id,
                        "(RFC822)",
                    )

                if status != "OK" or not rows:
                    continue

                raw = self._raw_message(rows)
                if not raw:
                    continue

                message = BytesParser(
                    policy=policy.default
                ).parsebytes(raw)

                if (
                    not uid_mode
                    and not self._message_is_recent(
                        message,
                        requested_floor,
                    )
                ):
                    continue

                subject = str(
                    message.get("Subject", "") or ""
                ).strip()
                date_value = str(
                    message.get("Date", "") or ""
                ).strip()

                progress(
                    (
                        66,
                        "E-mail da Gupy localizado via IMAP "
                        f"(UID: {numeric_id or 'n/d'}; "
                        f"assunto: {subject or 'sem assunto'}; "
                        f"data: {date_value or 'sem data'}).",
                    )
                )

                link = self._extract_magic_link(
                    message
                )
                if not link:
                    continue

                progress(
                    (
                        72,
                        "Link Acessar capturado "
                        "do novo e-mail da Gupy.",
                    )
                )
                return link

            return None

        finally:
            try:
                client.logout()
            except Exception as exc:
                logging.getLogger(__name__).debug("Falha ao encerrar a sessão IMAP: %s", exc)


    @staticmethod
    def _raw_message(rows: list[Any]) -> bytes | None:
        for row in rows:
            if isinstance(row, tuple) and len(row) >= 2:
                payload = row[1]
                if isinstance(payload, bytes):
                    return payload
        return None

    @classmethod
    def _extract_magic_link(cls, message: Message) -> str | None:
        html_parts: list[str] = []
        text_parts: list[str] = []

        if message.is_multipart():
            parts = message.walk()
        else:
            parts = (message,)

        for part in parts:
            content_type = part.get_content_type()
            if content_type not in {"text/html", "text/plain"}:
                continue

            try:
                content = part.get_content()
            except Exception:
                payload = part.get_payload(decode=True)
                if not isinstance(payload, bytes):
                    continue
                charset = part.get_content_charset() or "utf-8"
                content = payload.decode(charset, errors="replace")

            if content_type == "text/html":
                html_parts.append(str(content))
            else:
                text_parts.append(str(content))

        for html in html_parts:
            parser = _AnchorCollector()
            parser.feed(unescape(html))

            for href, text in parser.anchors:
                if "acessar" in text.casefold() and cls._is_gupy_url(href):
                    return unescape(href).strip()

            for href, _text in parser.anchors:
                if cls._is_gupy_url(href):
                    return unescape(href).strip()

        url_pattern = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
        for text in text_parts:
            for candidate in url_pattern.findall(text):
                if cls._is_gupy_url(candidate):
                    return candidate.rstrip(").,;")

        return None

    @staticmethod
    def _message_is_recent(
        message: Message,
        requested_floor: datetime,
    ) -> bool:
        raw_date = str(message.get("Date", "") or "").strip()
        if not raw_date:
            return True

        try:
            received = parsedate_to_datetime(raw_date)
        except (TypeError, ValueError, OverflowError):
            return True

        if received.tzinfo is None:
            received = received.replace(tzinfo=UTC)

        return received.astimezone(UTC) >= requested_floor

    @staticmethod
    def _normalize_requested_after(value: datetime) -> datetime:
        requested = value
        if requested.tzinfo is None:
            requested = requested.replace(tzinfo=UTC)
        return requested.astimezone(UTC) - timedelta(minutes=2)

    @staticmethod
    def _is_gupy_url(value: str) -> bool:
        try:
            parsed = urlparse(unescape(value).strip())
        except ValueError:
            return False

        host = (parsed.hostname or "").casefold()
        return bool(
            parsed.scheme == "https"
            and (
                host == "gupy.io"
                or host.endswith(".gupy.io")
                or host == "gupy.com.br"
                or host.endswith(".gupy.com.br")
            )
        )

    @staticmethod
    def _validate_configuration(
        credential: LoginCredential,
        password: str,
    ) -> None:
        missing = [
            label
            for label, value in (
                ("servidor IMAP", credential.server),
                ("usuário/e-mail", credential.username),
                ("pasta IMAP", credential.folder),
                ("senha", password),
            )
            if not str(value).strip()
        ]
        if missing:
            raise TerraImapGupyMagicLinkUnavailableError(
                "Configuração Terra IMAP incompleta: " + ", ".join(missing)
            )

    @staticmethod
    def _connect(credential: LoginCredential) -> imaplib.IMAP4:
        security = credential.security.strip().upper() or "SSL/TLS"
        port = int(
            credential.port
            or (993 if security == "SSL/TLS" else 143)
        )
        timeout = max(int(credential.timeout_seconds or 60), 1)
        host = credential.server.strip()

        if security == "SSL/TLS":
            return imaplib.IMAP4_SSL(host, port, timeout=timeout)

        client = imaplib.IMAP4(host, port, timeout=timeout)
        if security == "STARTTLS":
            client.starttls()
        elif security != "NENHUMA":
            client.logout()
            raise TerraImapGupyMagicLinkUnavailableError(
                "Segurança IMAP inválida."
            )
        return client
