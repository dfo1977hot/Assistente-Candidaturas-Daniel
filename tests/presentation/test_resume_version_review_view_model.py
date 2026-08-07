"""Tests for ResumeVersionReviewViewModel mappings."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from acd.application.query_ports import GeneratedResumeVersionQueryDTO
from acd.application.resume_version_review_use_case import (
    ResumeVersionReviewResult,
    ResumeVersionReviewStatus,
)
from acd.presentation.pages.resume_version_review_view_model import ResumeVersionReviewViewModel


class _UseCase:
    def __init__(self, result: ResumeVersionReviewResult) -> None:
        self.result = result
        self.calls: list[tuple[int, int | None]] = []

    def execute(
        self,
        application_id: int,
        selected_version_id: int | None = None,
    ) -> ResumeVersionReviewResult:
        self.calls.append((application_id, selected_version_id))
        return self.result


def _version() -> GeneratedResumeVersionQueryDTO:
    return GeneratedResumeVersionQueryDTO(
        version_id=8,
        curriculum_id=4,
        version="v8",
        content="Versão selecionada",
        explanation="Explicação persistida",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_maps_success_and_forwards_visual_selection() -> None:
    version = _version()
    use_case = _UseCase(
        ResumeVersionReviewResult(
            ResumeVersionReviewStatus.SUCCESS,
            application_id=11,
            curriculum_id=4,
            original_content="Original",
            versions=(version,),
            selected_version=version,
        )
    )
    view_model = ResumeVersionReviewViewModel(use_case)  # type: ignore[arg-type]

    state = view_model.load(11)
    selected_state = view_model.select_version(11, 8)

    assert use_case.calls == [(11, None), (11, 8)]
    assert state.title == "Versões deste currículo"
    assert state.original_content == "Original"
    assert state.versions[0].label == "v8"
    assert selected_state.selected_content == "Versão selecionada"
    assert selected_state.explanation == "Explicação persistida"


@pytest.mark.parametrize(
    "status",
    [
        ResumeVersionReviewStatus.APPLICATION_NOT_FOUND,
        ResumeVersionReviewStatus.CURRICULUM_REQUIRED,
        ResumeVersionReviewStatus.NO_VERSIONS,
        ResumeVersionReviewStatus.VERSION_NOT_FOUND,
    ],
)
def test_maps_functional_statuses(status: ResumeVersionReviewStatus) -> None:
    use_case = _UseCase(ResumeVersionReviewResult(status, application_id=11))

    state = ResumeVersionReviewViewModel(use_case).load(11)  # type: ignore[arg-type]

    assert state.status == status.value
    assert state.message
