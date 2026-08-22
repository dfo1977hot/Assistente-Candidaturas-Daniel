from pathlib import Path

SOURCE = Path(
    "acd/infrastructure/email/"
    "terra_imap_gupy_magic_link_service.py"
).read_text(encoding="utf-8")


def test_runtime_folder_comes_only_from_configuration() -> None:
    assert "credential.folder.strip()" in SOURCE
    assert "client.select(" in SOURCE
    assert "mailbox," in SOURCE
    assert "readonly=True," in SOURCE

    assert 'folder="Gupy"' not in SOURCE
    assert 'folder="INBOX"' not in SOURCE


def test_inbox_is_only_normalized_at_runtime() -> None:
    assert 'mailbox.casefold() == "inbox"' in SOURCE
    assert 'mailbox = "INBOX"' in SOURCE
