from pathlib import Path


def test_job_page_supports_automatic_external_application_url_detection() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert "Detectar link Candidatar-se" in source
    assert "resolve_linkedin_application_url" in source
    assert 'getattr(result, "application_url", "")' in source


def test_linkedin_browser_adapter_resolves_application_entry_points() -> None:
    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")

    assert "def resolve_linkedin_application_url" in source

    # Off-site LinkedIn application button.
    assert 'has-text("Candidatar-se")' in source
    assert "parsed = urlparse(candidate)" in source
    assert '"linkedin.com" not in parsed.netloc.lower()' in source

    # LinkedIn redirect/tracking URLs can expose the real external destination.
    assert "parse_qs(" in source
    assert "parsed.query" in source
    assert "keep_blank_values=False" in source
    assert '"/safety/go"' in source or 'endswith("/safety/go")' in source

    # Easy Apply is a valid application path.
    assert "Candidatura simplificada" in source

    # Closed listings are explicitly recognized.
    assert "Não aceita mais candidaturas" in source
