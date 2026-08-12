from pathlib import Path


def test_detection_does_not_open_destination_in_default_browser() -> None:
    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")
    start = source.index("    def resolve_linkedin_application_url(")
    end = source.index("    def _prepare_gupy(", start)
    method = source[start:end]

    assert "_open_default_browser(external_url)" not in method
    assert "_open_default_browser(job_url)" not in method


def test_visible_apply_control_is_not_treated_as_closed_when_url_is_unresolved() -> None:
    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")
    assert "if self._linkedin_has_external_apply_control(page):" in source
    assert 'application_type="external_unresolved"' in source
    assert "accepting_applications=True" in source


def test_job_page_only_fills_application_url_without_opening_it() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")
    assert "self.application_url_input.setText(application_url)" in source
    assert "Link Candidatar-se localizado." in source
    assert "localizado e aberto" not in source
