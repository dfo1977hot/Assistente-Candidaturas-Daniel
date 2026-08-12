from pathlib import Path

from acd.services.assisted_application_service import (
    ApplicantProfile,
    ApplicantProfileStore,
    AssistedApplicationResult,
    AssistedApplicationService,
)


class _Browser:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def prepare(self, **kwargs: object) -> AssistedApplicationResult:
        self.calls.append(kwargs)
        return AssistedApplicationResult(
            platform="Gupy",
            url=str(kwargs["url"]),
            fields_filled=3,
            resume_attached=True,
            linkedin_restricted_mode=False,
            source_url_opened=True,
        )


def test_prepare_passes_linkedin_source_and_gupy_target(tmp_path: Path) -> None:
    browser = _Browser()
    service = AssistedApplicationService(
        browser,
        ApplicantProfileStore(tmp_path / "profile.json"),
    )

    result = service.prepare(
        job_url="https://3coracoes.gupy.io/job/example",
        source_url="https://www.linkedin.com/jobs/view/123/",
        profile=ApplicantProfile("Daniel", "daniel@example.com"),
        resume_path=tmp_path / "curriculo.docx",
    )

    assert result.platform == "Gupy"
    assert browser.calls[0]["url"] == "https://3coracoes.gupy.io/job/example"
    assert browser.calls[0]["source_url"] == "https://www.linkedin.com/jobs/view/123/"


def test_prepare_accepts_gupy_without_source_url(tmp_path: Path) -> None:
    browser = _Browser()
    service = AssistedApplicationService(
        browser,
        ApplicantProfileStore(tmp_path / "profile.json"),
    )

    service.prepare(
        job_url="https://empresa.gupy.io/job/abc",
        profile=ApplicantProfile("Daniel", "daniel@example.com"),
        resume_path=None,
    )

    assert browser.calls[0]["source_url"] is None
