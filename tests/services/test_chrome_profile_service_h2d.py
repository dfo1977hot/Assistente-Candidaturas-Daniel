from __future__ import annotations

from pathlib import Path
import subprocess

from acd.services.chrome_profile_service import ChromeProfileService


def test_chrome_profile_uses_dedicated_acd_directory() -> None:
    assert ChromeProfileService.PROFILE_DIR == Path("data/browser_profiles/acd_chrome")


def test_open_google_authentication_never_receives_a_password(
    tmp_path: Path,
    monkeypatch,
) -> None:
    service = ChromeProfileService()
    executable = tmp_path / "chrome.exe"
    executable.write_text("", encoding="utf-8")
    monkeypatch.setattr(service, "chrome_executable", lambda: executable)
    monkeypatch.setattr(service, "profile_dir", lambda: tmp_path / "profile")

    calls: list[list[str]] = []

    class _Process:
        pass

    def fake_popen(args, **_kwargs):
        calls.append(list(args))
        return _Process()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    service.open_for_google_authentication()

    assert calls
    command = calls[0]
    assert "https://accounts.google.com/" in command
    assert any(arg.startswith("--user-data-dir=") for arg in command)
    assert not any("password" in arg.casefold() or "senha" in arg.casefold() for arg in command)
