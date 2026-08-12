from pathlib import Path


def test_saved_jobs_headless_does_not_force_installed_chrome() -> None:
    source = Path(
        "acd/infrastructure/linkedin/linkedin_saved_jobs_browser.py"
    ).read_text(encoding="utf-8")

    assert "runs_headless = self._runs_headless()" in source
    assert 'if not runs_headless:' in source
    assert 'launch_options["channel"] = "chrome"' in source
    assert '"headless": runs_headless' in source


def test_installed_chrome_is_only_used_for_visible_mode() -> None:
    source = Path(
        "acd/infrastructure/linkedin/linkedin_saved_jobs_browser.py"
    ).read_text(encoding="utf-8")

    block_start = source.index("runs_headless = self._runs_headless()")
    block_end = source.index(
        "context = playwright.chromium.launch_persistent_context",
        block_start,
    )
    block = source[block_start:block_end]

    assert 'channel="chrome"' not in block
    assert 'if not runs_headless:' in block
