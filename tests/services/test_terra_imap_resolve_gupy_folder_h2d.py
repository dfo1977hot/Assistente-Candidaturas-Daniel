from acd.services.settings_service import SettingsService


class FakeImap:
    def __init__(self, rows):
        self.rows = rows

    def list(self):
        return 'OK', self.rows


def test_resolves_inbox_slash_gupy() -> None:
    client = FakeImap([
        b'(\\HasNoChildren) "/" "INBOX"',
        b'(\\HasNoChildren) "/" "INBOX/Gupy"',
    ])
    assert SettingsService._resolve_imap_folder(client, 'Gupy') == 'INBOX/Gupy'


def test_resolves_inbox_dot_gupy() -> None:
    client = FakeImap([b'(\\HasNoChildren) "." "INBOX.Gupy"'])
    assert SettingsService._resolve_imap_folder(client, 'Gupy') == 'INBOX.Gupy'


def test_resolves_exact_gupy() -> None:
    client = FakeImap([b'(\\HasNoChildren) "/" "Gupy"'])
    assert SettingsService._resolve_imap_folder(client, 'Gupy') == 'Gupy'
