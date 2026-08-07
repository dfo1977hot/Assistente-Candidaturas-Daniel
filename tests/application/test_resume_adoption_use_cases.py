from __future__ import annotations

from datetime import datetime

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.composition.read_models import ApplicationContext
from acd.application.query_ports import GeneratedResumeVersionQueryDTO
from acd.application.resume_adoption_use_cases import (
    AdoptResumeVersionRequest,
    AdoptResumeVersionUseCase,
    ResumeAdoptionStatus,
    UseOriginalResumeRequest,
    UseOriginalResumeUseCase,
)


class FakeApplicationContextService:
    def __init__(self, applications: dict[int, ApplicationContext]) -> None:
        self.applications = applications

    def build(self, application_id: int) -> ApplicationContext | None:
        return self.applications.get(application_id)


class FakeGeneratedResumeVersionQueryPort:
    def __init__(self, versions: dict[int, tuple[GeneratedResumeVersionQueryDTO, ...]]) -> None:
        self.versions = versions

    def list_by_curriculum_id(
        self, curriculum_id: int
    ) -> tuple[GeneratedResumeVersionQueryDTO, ...]:
        return self.versions.get(curriculum_id, ())


class FakeSelectionPort:
    def __init__(self) -> None:
        self.set_calls: list[tuple[int, int]] = []
        self.clear_calls: list[int] = []

    def set_selected_resume_version(self, application_id: int, resume_version_id: int) -> bool:
        self.set_calls.append((application_id, resume_version_id))
        return True

    def clear_selected_resume_version(self, application_id: int) -> bool:
        self.clear_calls.append(application_id)
        return True


def _application(
    curriculum_id: int | None = 10, selected_resume_version_id: int | None = None
) -> ApplicationContext:
    return ApplicationContext(
        application_id=1,
        job_id=2,
        company_id=3,
        status="Draft",
        curriculum_id=curriculum_id,
        selected_resume_version_id=selected_resume_version_id,
        resume_source=ApplicationResumeSource.from_selection(selected_resume_version_id),
    )


def _version(version_id: int = 20, curriculum_id: int = 10) -> GeneratedResumeVersionQueryDTO:
    return GeneratedResumeVersionQueryDTO(
        version_id=version_id,
        curriculum_id=curriculum_id,
        version="v2",
        content="unchanged content",
        explanation="unchanged explanation",
        created_at=datetime(2026, 1, 1),
    )


def test_adopt_persists_only_a_version_from_the_application_curriculum() -> None:
    selection_port = FakeSelectionPort()
    use_case = AdoptResumeVersionUseCase(
        FakeApplicationContextService({1: _application()}),
        FakeGeneratedResumeVersionQueryPort({10: (_version(),)}),
        selection_port,
    )

    result = use_case.execute(AdoptResumeVersionRequest(1, 20))

    assert result.status is ResumeAdoptionStatus.SUCCESS
    assert result.resume_source is ApplicationResumeSource.RESUME_VERSION
    assert result.selected_resume_version_id == 20
    assert selection_port.set_calls == [(1, 20)]


def test_adopt_rejects_missing_application_curriculum_or_external_version() -> None:
    selection_port = FakeSelectionPort()
    use_case = AdoptResumeVersionUseCase(
        FakeApplicationContextService({1: _application(None), 2: _application()}),
        FakeGeneratedResumeVersionQueryPort({10: (_version(21, 99),)}),
        selection_port,
    )

    assert use_case.execute(AdoptResumeVersionRequest(3, 20)).status is ResumeAdoptionStatus.APPLICATION_NOT_FOUND
    assert use_case.execute(AdoptResumeVersionRequest(1, 20)).status is ResumeAdoptionStatus.CURRICULUM_REQUIRED
    assert use_case.execute(AdoptResumeVersionRequest(2, 20)).status is ResumeAdoptionStatus.VERSION_NOT_FOUND
    assert selection_port.set_calls == []


def test_adopt_is_idempotent_when_the_requested_version_is_already_selected() -> None:
    selection_port = FakeSelectionPort()
    use_case = AdoptResumeVersionUseCase(
        FakeApplicationContextService({1: _application(selected_resume_version_id=20)}),
        FakeGeneratedResumeVersionQueryPort({10: (_version(),)}),
        selection_port,
    )

    result = use_case.execute(AdoptResumeVersionRequest(1, 20))

    assert result.status is ResumeAdoptionStatus.ALREADY_SELECTED
    assert selection_port.set_calls == []


def test_use_original_clears_selection_and_is_idempotent() -> None:
    selection_port = FakeSelectionPort()
    selected = UseOriginalResumeUseCase(
        FakeApplicationContextService({1: _application(selected_resume_version_id=20)}), selection_port
    )
    original = UseOriginalResumeUseCase(
        FakeApplicationContextService({1: _application()}), selection_port
    )

    result = selected.execute(UseOriginalResumeRequest(1))

    assert result.status is ResumeAdoptionStatus.SUCCESS
    assert result.resume_source is ApplicationResumeSource.ORIGINAL
    assert selection_port.clear_calls == [1]
    assert original.execute(UseOriginalResumeRequest(1)).status is ResumeAdoptionStatus.SUCCESS
    assert selection_port.clear_calls == [1]
