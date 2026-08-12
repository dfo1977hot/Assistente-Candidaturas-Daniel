from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

from acd.infrastructure.email.gupy_magic_link_service import GupyMagicLinkService


class _CredentialStore:
    def __init__(self) -> None:
        self.value: str | None = None

    def get_password(self, _email: str) -> str | None:
        return self.value

    def set_password(self, _email: str, password: str) -> None:
        self.value = password


def test_credential_is_delegated_to_secure_store() -> None:
    store = _CredentialStore()
    service = GupyMagicLinkService(credential_store=store)  # type: ignore[arg-type]

    assert not service.has_credential("dfo1977@terra.com.br")
    service.save_credential("dfo1977@terra.com.br", "secret")
    assert service.has_credential("dfo1977@terra.com.br")


def test_only_recent_gupy_link_is_accepted() -> None:
    service = GupyMagicLinkService(credential_store=_CredentialStore())  # type: ignore[arg-type]
    message = EmailMessage()
    message["From"] = "no-reply@gupy.io"
    message["Subject"] = "Seu acesso à Gupy"
    message["Date"] = datetime.now(UTC)
    message.set_content("Acesse https://login.gupy.io/magic?token=abc123")

    link = service._validated_link(
        message,
        datetime.now(UTC) - timedelta(minutes=1),
    )

    assert link == "https://login.gupy.io/magic?token=abc123"


def test_old_message_is_rejected() -> None:
    service = GupyMagicLinkService(credential_store=_CredentialStore())  # type: ignore[arg-type]
    message = EmailMessage()
    message["From"] = "no-reply@gupy.io"
    message["Subject"] = "Seu acesso"
    message["Date"] = datetime.now(UTC) - timedelta(minutes=10)
    message.set_content("https://login.gupy.io/magic?token=old")

    assert service._validated_link(message, datetime.now(UTC)) is None
