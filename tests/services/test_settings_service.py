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


def test_imap_metadata_persists_without_password_in_json(
    tmp_path: Path,
    monkeypatch,
) -> None:
    service = SettingsService(tmp_path / "settings.json")
    keyring = FakeKeyring()
    monkeypatch.setattr(service, "_keyring", lambda: keyring)

    credential = LoginCredential(
        service="Terra IMAP",
        username="dfo1977@terra.com.br",
        server="imap.example.test",
        port=993,
        security="SSL/TLS",
        folder="Gupy",
        timeout_seconds=60,
    )
    service.save_login(credential, "imap-secret")

    raw = (tmp_path / "settings.json").read_text(encoding="utf-8")
    saved = service.get_login("Terra IMAP")

    assert saved is not None
    assert saved.server == "imap.example.test"
    assert saved.port == 993
    assert saved.security == "SSL/TLS"
    assert saved.folder == "Gupy"
    assert saved.timeout_seconds == 60
    assert service.login_password("Terra IMAP") == "imap-secret"
    assert "imap-secret" not in raw


def test_ai_provider_settings_and_gemini_key_are_persisted_safely(
    tmp_path: Path,
    monkeypatch,
) -> None:
    service = SettingsService(tmp_path / "settings.json")
    keyring = FakeKeyring()
    monkeypatch.setattr(service, "_keyring", lambda: keyring)

    service.set_ai_provider_order(["ollama", "gemini", "openai"])
    service.set_ollama_base_url("http://localhost:11434")
    service.set_ai_model("ollama", "qwen3:8b")
    service.set_ai_model("gemini", "gemini-3.6-flash")
    service.set_ai_model("openai", "gpt-5-mini")
    service.set_api_key("gemini", "gemini-secret")

    raw = (tmp_path / "settings.json").read_text(encoding="utf-8")

    assert service.ai_provider_order() == ("ollama", "gemini", "openai")
    assert service.ollama_base_url() == "http://localhost:11434"
    assert service.ai_model("ollama") == "qwen3:8b"
    assert service.ai_model("gemini") == "gemini-3.6-flash"
    assert service.ai_model("openai") == "gpt-5-mini"
    assert service.get_api_key("gemini") == "gemini-secret"
    assert "gemini-secret" not in raw


def test_ai_provider_defaults_prefer_free_local_path(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")

    assert service.ai_provider_order() == ("ollama", "gemini", "openai")
    assert service.ollama_base_url() == "http://localhost:11434"
    assert service.ai_model("ollama") == "qwen3:8b"
