from pathlib import Path

from acd.infrastructure.application_automation.playwright_application_browser import (
    PlaywrightApplicationBrowser,
)
from acd.services.assisted_application_service import ApplicantProfile


def test_linkedin_opens_default_browser_and_returns_immediately(monkeypatch) -> None:
    opened: list[tuple[str, int]] = []
    progress: list[object] = []

    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_open_default_browser",
        staticmethod(lambda url: opened.append((url, 2)) or True),
    )

    result = PlaywrightApplicationBrowser().prepare(
        url="https://www.linkedin.com/jobs/view/4438490979/",
        profile=ApplicantProfile("Daniel", "daniel@example.com"),
        resume_path=Path("curriculo.docx"),
        progress=progress.append,
    )

    assert opened == [("https://www.linkedin.com/jobs/view/4438490979/", 2)]
    assert result.platform == "LinkedIn"
    assert result.linkedin_restricted_mode is True
    assert result.fields_filled == 0
    assert result.resume_attached is False
    assert progress[-1] == (100, "LinkedIn aberto para revisão manual")


def test_linkedin_reports_default_browser_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        PlaywrightApplicationBrowser,
        "_open_default_browser",
        staticmethod(lambda _url: False),
    )

    try:
        PlaywrightApplicationBrowser().prepare(
            url="https://www.linkedin.com/jobs/view/4438490979/",
            profile=ApplicantProfile("Daniel", "daniel@example.com"),
            resume_path=None,
            progress=lambda _payload: None,
        )
    except RuntimeError as error:
        assert "navegador padrão" in str(error)
    else:
        raise AssertionError("RuntimeError esperado")
