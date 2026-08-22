from pathlib import Path

SETTINGS = Path("acd/services/settings_service.py").read_text(encoding="utf-8")
PAGE = Path("acd/presentation/pages/settings_page.py").read_text(encoding="utf-8")


def test_imap_test_selects_configured_folder() -> None:
    assert "folder = credential.folder.strip()" in SETTINGS
    assert "client.select(mailbox, readonly=True)" in SETTINGS


def test_settings_page_no_longer_suggests_gupy_as_imap_folder() -> None:
    assert 'self.login_folder.setPlaceholderText("INBOX")' in PAGE
