from pathlib import Path

from acd.services.settings_service import LoginCredential, SettingsService


class FakeKeyring:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, account: str) -> str | None:
        return self.values.get((service, account))

    def set_password(self, service: str, account: str, value: str) -> None:
        self.values[(service, account)] = value

    def delete_password(self, service: str, account: str) -> None:
        self.values.pop((service, account), None)


def test_settings_persist_startup_mode_and_login_metadata(tmp_path: Path, monkeypatch) -> None:
    service = SettingsService(tmp_path / "settings.json")
    keyring = FakeKeyring()
    monkeypatch.setattr(service, "_keyring", lambda: keyring)

    service.set_startup_mode("minimized")
    service.set_browser_headless(True)
    service.set_api_key("openai", "sk-test")
    service.save_login(
        LoginCredential("LinkedIn", "https://linkedin.com", "daniel@example.com", "principal"),
        "secret",
    )

    reloaded = SettingsService(tmp_path / "settings.json")
    monkeypatch.setattr(reloaded, "_keyring", lambda: keyring)

    assert reloaded.startup_mode() == "minimized"
    assert reloaded.browser_headless() is True
    assert reloaded.get_api_key("openai") == "sk-test"
    assert reloaded.list_logins()[0].service == "LinkedIn"
    assert reloaded.login_password("LinkedIn") == "secret"


def test_browser_headless_defaults_to_visible(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    assert service.browser_headless() is False
