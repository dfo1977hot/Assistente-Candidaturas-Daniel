from __future__ import annotations

from dataclasses import dataclass

from acd.services.ats_service import ATSService


@dataclass
class _Score:
    id: int
    application_id: int
    curriculum_id: int
    job_profile_id: int | None
    total_score: float


class _Repository:
    def __init__(self) -> None:
        self.scores: list[object] = []
        self.details: list[object] = []
        self.gaps: list[object] = []
        self.recommendations: list[object] = []

    def get_latest_for_match(self, *, application_id: int, curriculum_id: int):
        for score in reversed(self.scores):
            if (
                score.application_id == application_id
                and score.curriculum_id == curriculum_id
            ):
                return score
        return None

    def save_score(self, score):
        score.id = len(self.scores) + 1
        self.scores.append(score)
        return score

    def save_detail(self, detail):
        self.details.append(detail)
        return detail

    def save_gap(self, gap):
        self.gaps.append(gap)
        return gap

    def save_recommendation(self, recommendation):
        self.recommendations.append(recommendation)
        return recommendation


class _Result:
    ats_score = 82.0
    score = 74.0
    missing_keywords = ("sap", "power bi")


def test_resume_match_is_persisted_as_reusable_ats_history() -> None:
    repository = _Repository()
    service = ATSService(repository=repository)

    saved = service.persist_resume_match_result(
        application_id=11,
        curriculum_id=7,
        result=_Result(),
    )

    assert saved.application_id == 11
    assert saved.curriculum_id == 7
    assert saved.total_score == 82.0
    assert len(repository.details) == 2
    assert [gap.skill_name for gap in repository.gaps] == ["sap", "power bi"]


def test_equal_resume_match_does_not_create_duplicate_ats_score() -> None:
    repository = _Repository()
    service = ATSService(repository=repository)

    first = service.persist_resume_match_result(
        application_id=11,
        curriculum_id=7,
        result=_Result(),
    )
    second = service.persist_resume_match_result(
        application_id=11,
        curriculum_id=7,
        result=_Result(),
    )

    assert second is first
    assert len(repository.scores) == 1
