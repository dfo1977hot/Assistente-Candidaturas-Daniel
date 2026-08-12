from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)


def test_linkedin_safety_go_url_is_unwrapped_to_vagas_com() -> None:
    wrapped = (
        "https://www.linkedin.com/safety/go/?"
        "url=https%3A%2F%2Fwww.vagas.com.br%2Fvagas%2Fv2826099"
        "%3Ffnt%3D19%26fntcompl%3Dlinkedin%26utm_campaign%3Djobs"
        "%26utm_content%3DAnalista%2520de%2520Planejamento%2520e%2520Controle"
        "%2520de%2520Produ%25e7%25e3o%2520Sr%26utm_medium%3Dxml"
        "%26utm_source%3Dlinkedin"
        "&urlhash=WqUa&isSdui=true"
    )

    resolved = PlaywrightApplicationBrowser._normalize_external_application_url(
        wrapped
    )

    assert resolved.startswith("https://www.vagas.com.br/vagas/v2826099?")
    assert "utm_source=linkedin" in resolved


def test_unknown_detection_is_non_destructive() -> None:
    from pathlib import Path

    browser_source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")
    page_source = Path("acd/presentation/pages/job_page.py").read_text(
        encoding="utf-8"
    )

    assert 'application_type="unknown"' in browser_source
    assert "accepting_applications=None" in browser_source
    assert "resolution.accepting_applications is None" in page_source
    assert "A vaga não será excluída." in page_source
