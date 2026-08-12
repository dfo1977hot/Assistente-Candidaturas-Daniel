from pathlib import Path


def test_job_page_accepts_injected_application_url_resolver() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert (
        "application_url_resolver: LinkedInApplicationResolver | None = None"
        in source
    )
    assert (
        "application_url_resolver or UnavailableLinkedInApplicationResolver()"
        in source
    )


def test_composition_root_injects_runtime_headless_setting_into_job_page() -> None:
    source = Path("acd/desktop_composition_root.py").read_text(encoding="utf-8")

    job_page_start = source.index('"jobs": JobPage(')
    job_page_end = source.index('"applications": application_page', job_page_start)
    block = source[job_page_start:job_page_end]

    assert "PlaywrightApplicationBrowser(" in block
    assert "linkedin_headless=settings_service.browser_headless" in block
