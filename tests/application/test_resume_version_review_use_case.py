"""Tests for the read-only resume version review use case."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from acd.application.composition.read_models import ApplicationContext, ResumeContext
from acd.application.query_ports import GeneratedResumeVersionQueryDTO
from acd.application.resume_version_review_use_case import (
    ResumeVersionReviewStatus,
    ResumeVersionReviewUseCase,
)


class _ApplicationContexts:
    def __init__(self, applications: dict[int, ApplicationContext]) -> None:
        self._applications = applications

    def build(self, application_id: int) -> ApplicationContext | None:
        return self._applications.get(application_id)


class _ResumeContexts:
    def __init__(self, resumes: dict[int, ResumeContext]) -> None:
        self._resumes = resumes

    def build(self, curriculum_id: int) -> ResumeContext | None:
        return self._resumes.get(curriculum_id)


class _VersionPort:
    def __init__(self, versions: dict[int, tuple[GeneratedResumeVersionQueryDTO, ...]]) -> None:
        self._versions = versions
        self.calls: list[int] = []

    def list_by_curriculum_id(
        self,
        curriculum_id: int,
    ) -> tuple[GeneratedResumeVersionQueryDTO, ...]:
        self.calls.append(curriculum_id)
        return self._versions.get(curriculum_id, ())


def _version(version_id: int, curriculum_id: int, version: str) -> GeneratedResumeVersionQueryDTO:
    return GeneratedResumeVersionQueryDTO(
        version_id=version_id,
        curriculum_id=curriculum_id,
        version=version,
        content=f"Conteúdo {version}",
        explanation=f"Explicação {version}",
        created_at=datetime(2026, 1, version_id, tzinfo=UTC),
    )


@pytest.fixture
def version_port() -> _VersionPort:
    return _VersionPort({10: (_version(1, 10, "v1"), _version(2, 10, "v2")), 20: (_version(3, 20, "v1"),)})


def _use_case(version_port: _VersionPort) -> ResumeVersionReviewUseCase:
    return ResumeVersionReviewUseCase(
        _ApplicationContexts(
            {
                1: ApplicationContext(1, 2, 3, "Draft", curriculum_id=10),
                2: ApplicationContext(2, 2, 3, "Draft", curriculum_id=None),
                3: ApplicationContext(3, 2, 3, "Draft", curriculum_id=30),
                4: ApplicationContext(4, 2, 3, "Draft", curriculum_id=40),
            }
        ),
        _ResumeContexts(
            {
                10: ResumeContext(10, "v1", "Original currículo 10"),
                40: ResumeContext(40, "v1", "Original currículo 40"),
            }
        ),
        version_port,
    )


def test_loads_latest_version_and_only_linked_curriculum(version_port: _VersionPort) -> None:
    result = _use_case(version_port).execute(1)

    assert result.status is ResumeVersionReviewStatus.SUCCESS
    assert result.original_content == "Original currículo 10"
    assert [version.version_id for version in result.versions] == [1, 2]
    assert result.selected_version is not None
    assert result.selected_version.version_id == 2
    assert version_port.calls == [10]


@pytest.mark.parametrize(
    ("application_id", "status"),
    [
        (99, ResumeVersionReviewStatus.APPLICATION_NOT_FOUND),
        (2, ResumeVersionReviewStatus.CURRICULUM_REQUIRED),
        (3, ResumeVersionReviewStatus.CURRICULUM_REQUIRED),
    ],
)
def test_returns_functional_status_for_unavailable_context(
    version_port: _VersionPort,
    application_id: int,
    status: ResumeVersionReviewStatus,
) -> None:
    result = _use_case(version_port).execute(application_id)

    assert result.status is status
    assert result.versions == ()


def test_returns_no_versions_without_writing(version_port: _VersionPort) -> None:
    result = _use_case(version_port).execute(4)

    assert result.status is ResumeVersionReviewStatus.NO_VERSIONS
    assert result.original_content == "Original currículo 40"
    assert result.versions == ()


def test_selects_only_version_from_the_application_curriculum(version_port: _VersionPort) -> None:
    result = _use_case(version_port).execute(1, selected_version_id=1)
    foreign_version = _use_case(version_port).execute(1, selected_version_id=3)

    assert result.status is ResumeVersionReviewStatus.SUCCESS
    assert result.selected_version is not None
    assert result.selected_version.explanation == "Explicação v1"
    assert foreign_version.status is ResumeVersionReviewStatus.VERSION_NOT_FOUND
    assert [version.version_id for version in foreign_version.versions] == [1, 2]
