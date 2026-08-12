from pathlib import Path

import pytest

from acd.services.assisted_application_service import (
    ApplicantProfile,
    ApplicantProfileStore,
    AssistedApplicationResult,
    AssistedApplicationService,
)


class _Browser:
    def __init__(self) -> None:
        self.calls = []

    def prepare(self, **kwargs):
        self.calls.append(kwargs)
        return AssistedApplicationResult(
            platform="Greenhouse", url=kwargs["url"], fields_filled=2,
            resume_attached=True, linkedin_restricted_mode=False,
        )


def test_prepare_persists_profile_and_never_submits(tmp_path: Path) -> None:
    browser = _Browser()
    store = ApplicantProfileStore(tmp_path / "profile.json")
    service = AssistedApplicationService(browser, store)
    profile = ApplicantProfile("Daniel", "daniel@example.com")
    result = service.prepare(
        job_url="https://boards.greenhouse.io/example/jobs/1",
        profile=profile, resume_path=tmp_path / "cv.pdf",
    )
    assert result.platform == "Greenhouse"
    assert store.load() == profile
    assert len(browser.calls) == 1


def test_prepare_rejects_invalid_url(tmp_path: Path) -> None:
    service = AssistedApplicationService(_Browser(), ApplicantProfileStore(tmp_path / "p.json"))
    with pytest.raises(ValueError, match="URL válida"):
        service.prepare(job_url="sem-url", profile=ApplicantProfile("Daniel", "d@e.com"), resume_path=None)
