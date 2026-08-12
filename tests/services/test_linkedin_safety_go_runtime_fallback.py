from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)

MARJAN_SAFETY_URL = (
    "https://www.linkedin.com/safety/go/?url="
    "https%3A%2F%2Fwww.vagas.com.br%2Fvagas%2Fv2826099"
    "%3Ffnt%3D19%26fntcompl%3Dlinkedin%26utm_campaign%3Djobs"
    "%26utm_content%3DAnalista%2520de%2520Planejamento%2520e%2520Controle"
    "%2520de%2520Produ%25e7%25e3o%2520Sr%26utm_medium%3Dxml"
    "%26utm_source%3Dlinkedin"
    "&urlhash=WqUa&isSdui=true"
)


def test_extracts_marjan_link_from_plain_html() -> None:
    html = f'<a class="apply" href="{MARJAN_SAFETY_URL}">Candidatar-se</a>'
    result = PlaywrightApplicationBrowser._extract_external_application_url_from_text(
        html,
        "https://www.linkedin.com/jobs/view/4441755053/",
    )
    assert result.startswith("https://www.vagas.com.br/vagas/v2826099?")
    assert "utm_source=linkedin" in result


def test_extracts_marjan_link_from_html_escaped_markup() -> None:
    escaped = (
        '<a href="https://www.linkedin.com/safety/go/?url='
        'https%3A%2F%2Fwww.vagas.com.br%2Fvagas%2Fv2826099'
        '%3Ffnt%3D19%26utm_source%3Dlinkedin&amp;urlhash=WqUa">'
        "Candidatar-se</a>"
    )
    result = PlaywrightApplicationBrowser._extract_external_application_url_from_text(
        escaped,
        "https://www.linkedin.com/jobs/view/4441755053/",
    )
    assert result.startswith("https://www.vagas.com.br/vagas/v2826099?")
    assert "utm_source=linkedin" in result


def test_runtime_has_dom_and_public_html_fallbacks() -> None:
    from pathlib import Path

    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")
    assert "_linkedin_external_url_from_page_content(page)" in source
    assert "_linkedin_external_url_from_public_html(job_url)" in source
    assert "page.content()" in source
    assert "urlopen(request, timeout=15)" in source
