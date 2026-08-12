from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)

BASE_URL = "https://www.linkedin.com/jobs/view/4443197584/"
FULL_URL = (
    "https://www.linkedin.com/jobs/view/4443197584/"
    "?trackingId=Yn3d%2BUyPTeWaQdWLA8%2FGbw%3D%3D"
)


def test_same_linkedin_job_accepts_tracking_url() -> None:
    assert PlaywrightApplicationBrowser._same_linkedin_job(FULL_URL, BASE_URL)


def test_same_linkedin_job_rejects_other_job() -> None:
    other = "https://www.linkedin.com/jobs/view/9999999999/?trackingId=x"
    assert not PlaywrightApplicationBrowser._same_linkedin_job(other, BASE_URL)


def test_easy_apply_runtime_uses_complete_page_url() -> None:
    from pathlib import Path

    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")

    assert "easy_apply_url = self._linkedin_easy_apply_url(page, job_url)" in source
    assert "current_url = str(getattr(page, \"url\", \"\") or \"\").strip()" in source
    assert "return current_url" in source
    assert "trackingId" not in source  # no hard-coded tracking token
