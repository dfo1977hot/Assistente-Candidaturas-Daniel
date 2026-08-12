from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)

BAUMINAS_URL = (
    "https://www.linkedin.com/safety/go/?url="
    "https%3A%2F%2Fgrupobauminas.gupy.io%2Fjobs%2F11984451"
    "%3FjobBoardSource%3Dgupy_public_page"
    "&urlhash=VPPv&isSdui=true"
)


def test_bauminas_safety_go_is_unwrapped() -> None:
    result = PlaywrightApplicationBrowser._normalize_external_application_url(
        BAUMINAS_URL
    )
    assert result == (
        "https://grupobauminas.gupy.io/jobs/11984451"
        "?jobBoardSource=gupy_public_page"
    )


def test_bauminas_link_is_extracted_from_html() -> None:
    html = f'<a href="{BAUMINAS_URL}">Candidatar-se</a>'
    result = PlaywrightApplicationBrowser._extract_external_application_url_from_text(
        html,
        "https://www.linkedin.com/jobs/view/11984451/",
    )
    assert result == (
        "https://grupobauminas.gupy.io/jobs/11984451"
        "?jobBoardSource=gupy_public_page"
    )


def test_runtime_uses_authenticated_context_request_fallback() -> None:
    from pathlib import Path

    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")

    assert "_linkedin_external_url_from_frames(page)" in source
    assert "_linkedin_external_url_from_context_request(" in source
    assert "context.request.get(" in source
    assert "page.frames" in source
