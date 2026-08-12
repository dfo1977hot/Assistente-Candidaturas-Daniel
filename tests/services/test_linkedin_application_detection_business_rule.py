from pathlib import Path


def test_browser_supports_external_and_easy_apply_actions() -> None:
    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")

    assert "Candidatar-se" in source
    assert "Candidatura simplificada" in source
    assert "Easy Apply" in source

    # Regra atual: detectar/preencher a URL, sem abrir o navegador padrão.
    assert "_open_default_browser(external_url)" not in source
    assert "_open_default_browser(job_url)" not in source
    assert "LinkedInApplicationResolution" in source


def test_job_page_does_not_open_detected_application_url() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert "self.application_url_input.setText(application_url)" in source
    assert "Link Candidatar-se localizado." in source
    assert "localizado e aberto" not in source
