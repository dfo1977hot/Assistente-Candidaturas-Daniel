from pathlib import Path

SOURCE = Path("acd/presentation/pages/settings_page.py").read_text(encoding="utf-8")


def test_terra_imap_defaults_to_inbox() -> None:
    assert 'self.login_folder.setText("INBOX")' in SOURCE
    assert 'self.login_server.setText("imap.terra.com.br")' in SOURCE


def test_non_imap_services_clear_stale_imap_fields() -> None:
    assert "self.login_server.clear()" in SOURCE
    assert "self.login_folder.clear()" in SOURCE
