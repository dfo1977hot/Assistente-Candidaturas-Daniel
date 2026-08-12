from pathlib import Path

from acd.services.company_lookup_service import (
    GooglePlacesCompanyLookupProvider,
    OpenAIWebCompanyLookupProvider,
)


def test_explicit_empty_company_keys_do_not_fall_back_to_saved_settings() -> None:
    assert OpenAIWebCompanyLookupProvider(api_key="").api_key == ""
    assert GooglePlacesCompanyLookupProvider(api_key="").api_key == ""


def test_presentation_has_no_infrastructure_import_for_linkedin_resolver() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")
    assert "acd.infrastructure" not in source
    assert "UnavailableLinkedInApplicationResolver" in source


def test_application_page_does_not_construct_resume_match_service() -> None:
    source = Path("acd/presentation/pages/application_page.py").read_text(
        encoding="utf-8"
    )
    assert "ResumeMatchService()" not in source


def test_linkedin_prepare_source_url_is_optional() -> None:
    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")
    assert "source_url: str | None = None" in source
