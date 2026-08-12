from pathlib import Path


def test_passwordless_automation_is_not_part_of_productive_gupy_path() -> None:
    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")
    gupy = source.index('if platform == "Gupy":')
    manual_return = source.index("return AssistedApplicationResult(", gupy)
    playwright = source.index("from playwright.sync_api import sync_playwright")
    assert gupy < manual_return < playwright
