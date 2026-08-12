from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_linkedin_saved_jobs_browser_uses_runtime_headless_setting() -> None:
    source = _read("acd/infrastructure/linkedin/linkedin_saved_jobs_browser.py")

    assert "headless: bool | Callable[[], bool] = False" in source
    assert "runs_headless = self._runs_headless()" in source
    assert '"headless": runs_headless' in source
    assert 'if not runs_headless:' in source
    assert 'launch_options["channel"] = "chrome"' in source


def test_visible_mode_uses_installed_chrome_only_when_not_headless() -> None:
    source = _read("acd/infrastructure/linkedin/linkedin_saved_jobs_browser.py")

    start = source.index("runs_headless = self._runs_headless()")
    end = source.index(
        "context = playwright.chromium.launch_persistent_context",
        start,
    )
    block = source[start:end]

    assert 'channel="chrome"' not in block
    assert 'launch_options["channel"] = "chrome"' in block
    assert "if not runs_headless:" in block
