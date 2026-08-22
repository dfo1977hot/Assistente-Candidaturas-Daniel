from datetime import UTC, datetime
from email.message import EmailMessage

from acd.infrastructure.email.terra_imap_gupy_magic_link_service import (
    TerraImapGupyMagicLinkService,
)


def test_accepts_gupy_email_redirect() -> None:
    assert TerraImapGupyMagicLinkService._is_gupy_url(
        "https://email.gupy.com.br/c/token"
    )


def test_extracts_access_anchor_from_html() -> None:
    message = EmailMessage()
    message["Date"] = "Mon, 17 Aug 2026 16:00:00 -0300"
    message.set_content("Fallback")
    message.add_alternative(
        '<html><a href="https://email.gupy.com.br/c/token">Acessar</a></html>',
        subtype="html",
    )

    assert (
        TerraImapGupyMagicLinkService._extract_magic_link(message)
        == "https://email.gupy.com.br/c/token"
    )


def test_recent_message_accepts_request_clock_skew() -> None:
    message = EmailMessage()
    message["Date"] = "Mon, 17 Aug 2026 16:00:00 -0300"

    floor = datetime(2026, 8, 17, 18, 59, tzinfo=UTC)

    assert TerraImapGupyMagicLinkService._message_is_recent(
        message,
        floor,
    )
