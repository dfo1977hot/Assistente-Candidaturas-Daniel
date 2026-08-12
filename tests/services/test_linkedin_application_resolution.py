from acd.infrastructure.application_automation.playwright_application_browser import (
    LinkedInApplicationResolution,
    PlaywrightApplicationBrowser,
)


def test_external_url_rejects_linkedin_and_accepts_external_http() -> None:
    assert not PlaywrightApplicationBrowser._is_external_application_url(
        "https://www.linkedin.com/jobs/view/123456789/"
    )
    assert PlaywrightApplicationBrowser._is_external_application_url(
        "https://careers.example.com/jobs/123"
    )


def test_resolution_represents_easy_apply() -> None:
    result = LinkedInApplicationResolution(
        url="https://www.linkedin.com/jobs/view/123456789/",
        application_type="easy_apply",
        accepting_applications=True,
    )
    assert result.application_type == "easy_apply"
    assert result.accepting_applications is True


def test_resolution_represents_closed_vacancy() -> None:
    result = LinkedInApplicationResolution(
        application_type="closed_no_action",
        accepting_applications=False,
    )
    assert result.url == ""
    assert result.accepting_applications is False
