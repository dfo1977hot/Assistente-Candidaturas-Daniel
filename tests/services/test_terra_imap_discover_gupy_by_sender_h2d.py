from acd.services.settings_service import SettingsService


class FakeImap:
    def __init__(self):
        self.selected = ""

    def list(self):
        return (
            "OK",
            [
                b'(\\HasNoChildren) "." "INBOX"',
                b'(\\HasNoChildren) "." "INBOX.Carreira Certa"',
                b'(\\HasNoChildren) "." "INBOX.Pasta123"',
            ],
        )

    def select(self, mailbox, readonly=True):
        del readonly
        self.selected = mailbox.strip('"')
        return "OK", [b"1"]

    def search(self, _charset, criterion, value):
        assert criterion == "FROM"
        assert value == '"no-reply@gupy.com.br"'
        if self.selected == "INBOX.Pasta123":
            return "OK", [b"101 102"]
        return "OK", [b""]


def test_finds_mailbox_by_sender_even_when_name_is_not_gupy() -> None:
    client = FakeImap()

    result = SettingsService._find_imap_mailbox_by_sender(
        client,
        "no-reply@gupy.com.br",
    )

    assert result == "INBOX.Pasta123"
