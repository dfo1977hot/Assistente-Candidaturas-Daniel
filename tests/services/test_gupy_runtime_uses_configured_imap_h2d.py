from pathlib import Path

BROWSER = Path(
    "acd/infrastructure/application_automation/"
    "playwright_application_browser.py"
).read_text(encoding="utf-8")

IMAP_SERVICE = Path(
    "acd/infrastructure/email/"
    "terra_imap_gupy_magic_link_service.py"
).read_text(encoding="utf-8")


def test_browser_uses_terra_imap_service_not_outlook() -> None:
    assert "TerraImapGupyMagicLinkService" in BROWSER
    assert "OutlookGupyMagicLinkService" not in BROWSER
    assert "Aguardando o e-mail de acesso da Gupy via IMAP" in BROWSER


def test_runtime_selects_folder_from_configuration() -> None:
    assert "credential.folder.strip()" in IMAP_SERVICE
    assert "client.select(" in IMAP_SERVICE
    assert "mailbox," in IMAP_SERVICE
    assert "readonly=True," in IMAP_SERVICE

    assert 'folder="Gupy"' not in IMAP_SERVICE
    assert 'folder="INBOX"' not in IMAP_SERVICE


def test_runtime_searches_expected_sender() -> None:
    assert 'EXPECTED_SENDER = "no-reply@gupy.com.br"' in IMAP_SERVICE
    assert '"FROM"' in IMAP_SERVICE
    assert "EXPECTED_SENDER" in IMAP_SERVICE


def test_runtime_supports_uid_baseline() -> None:
    assert "capture_sender_uid_baseline" in IMAP_SERVICE
    assert "min_uid" in IMAP_SERVICE
    assert "numeric_id <= min_uid" in IMAP_SERVICE
