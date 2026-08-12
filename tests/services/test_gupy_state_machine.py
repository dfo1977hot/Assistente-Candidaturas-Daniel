from pathlib import Path

SOURCE = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
).read_text(encoding="utf-8")


def test_gupy_opens_candidate_signin_in_default_browser() -> None:
    assert 'if platform == "Gupy":' in SOURCE
    assert 'login_url = f"{parsed.scheme}://{parsed.netloc}/candidates/signin"' in SOURCE
    assert "self._open_default_browser(login_url)" in SOURCE


def test_gupy_returns_before_playwright_automation() -> None:
    gupy = SOURCE.index('if platform == "Gupy":')
    playwright = SOURCE.index("from playwright.sync_api import sync_playwright")
    manual_return = SOURCE.index("return AssistedApplicationResult(", gupy)
    assert gupy < manual_return < playwright


def test_gupy_reports_manual_application() -> None:
    assert "Login da Gupy aberto para candidatura manual" in SOURCE
