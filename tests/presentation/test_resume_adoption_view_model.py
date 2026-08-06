from __future__ import annotations

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.resume_adoption_use_cases import (
    ResumeAdoptionResult,
    ResumeAdoptionStatus,
)
from acd.presentation.pages.resume_adoption_view_model import ResumeAdoptionViewModel


class _AdoptUseCase:
    def __init__(self) -> None:
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return ResumeAdoptionResult(
            ResumeAdoptionStatus.SUCCESS, request.application_id, 4,
            ApplicationResumeSource.RESUME_VERSION, request.resume_version_id, "selected"
        )


class _OriginalUseCase:
    def __init__(self) -> None:
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return ResumeAdoptionResult(
            ResumeAdoptionStatus.SUCCESS, request.application_id, 4,
            ApplicationResumeSource.ORIGINAL, None, "original"
        )


def test_explicit_commands_build_the_existing_requests() -> None:
    adopt = _AdoptUseCase()
    original = _OriginalUseCase()
    view_model = ResumeAdoptionViewModel(adopt, original)  # type: ignore[arg-type]

    adopted = view_model.adopt(3, 7)
    restored = view_model.use_original(3)

    assert (adopt.requests[0].application_id, adopt.requests[0].resume_version_id) == (3, 7)
    assert original.requests[0].application_id == 3
    assert adopted.resume_source is ApplicationResumeSource.RESUME_VERSION
    assert restored.resume_source is ApplicationResumeSource.ORIGINAL
