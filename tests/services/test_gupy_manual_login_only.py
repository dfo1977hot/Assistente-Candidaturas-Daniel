from pathlib import Path


def test_gupy_opens_only_the_manual_login_page() -> None:
    source = Path(
        "acd/infrastructure/application_automation/"
        "playwright_application_browser.py"
    ).read_text(encoding="utf-8")

    assert 'if platform == "Gupy":' in source
    assert 'login_url = f"{parsed.scheme}://{parsed.netloc}/candidates/signin"' in source
    assert '"Abrindo a página de login da Gupy"' in source
    assert '"Login da Gupy aberto para candidatura manual"' in source


def test_gupy_returns_before_playwright_automation() -> None:
    source = Path(
        "acd/infrastructure/application_automation/"
        "playwright_application_browser.py"
    ).read_text(encoding="utf-8")

    gupy_branch = source.index('if platform == "Gupy":')
    playwright_import = source.index("from playwright.sync_api import sync_playwright")

    assert gupy_branch < playwright_import
