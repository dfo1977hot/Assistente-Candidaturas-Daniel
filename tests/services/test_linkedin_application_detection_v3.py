from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)


def test_unwraps_linkedin_redirect_to_external_application() -> None:
    wrapped = (
        "https://www.linkedin.com/redir/redirect?"
        "url=https%3A%2F%2Fwww.vagas.com.br%2Fvagas%2Fv2826099"
    )
    assert (
        PlaywrightApplicationBrowser._normalize_external_application_url(wrapped)
        == "https://www.vagas.com.br/vagas/v2826099"
    )


def test_accepts_direct_external_application_url() -> None:
    url = "https://www.vagas.com.br/vagas/v2826099"
    assert (
        PlaywrightApplicationBrowser._normalize_external_application_url(url)
        == url
    )


def test_rejects_plain_linkedin_job_url_as_external() -> None:
    url = "https://www.linkedin.com/jobs/view/4441755053/"
    assert PlaywrightApplicationBrowser._normalize_external_application_url(url) == ""
