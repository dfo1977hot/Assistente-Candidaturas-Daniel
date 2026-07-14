"""Tests for GapAnalysisService."""

from __future__ import annotations

from types import SimpleNamespace

from acd.services.gap_analysis_service import GapAnalysisService


class FakeCareerRepository:
    """Fake repository."""

    def __init__(self) -> None:
        self.saved_gaps: list[dict] = []

    def get_goal(self, goal_id: int):
        if goal_id == 1:
            return SimpleNamespace(target_role="Supply Chain Manager")
        return None

    def create_gap(self, **kwargs):
        self.saved_gaps.append(kwargs)

    def list_gaps_by_goal(self, goal_id: int):
        return self.saved_gaps


class FakeRuleEngine:
    """Fake rule engine."""

    def analyze_compatibility(self, profile, target_role):
        return {
            "compatibility": 0.82,
            "gaps": [
                {
                    "skill": "Python",
                    "current": 2,
                    "required": 4,
                    "severity": "critical",
                },
                {
                    "skill": "Power BI",
                    "current": 3,
                    "required": 4,
                    "severity": "high",
                },
            ],
            "strengths": ["Excel"],
            "certificates_missing": ["PMP"],
        }

    def _estimate_learning_hours(self, delta):
        return delta * 20

    def generate_development_path(self, gaps):
        return gaps


def test_analyze_goal_success() -> None:
    """Should analyze a valid goal."""

    repository = FakeCareerRepository()

    service = GapAnalysisService(
        repository=repository,
        rule_engine=FakeRuleEngine(),
    )

    result = service.analyze_goal(
        goal_id=1,
        current_profile={},
    )

    assert result["goal_id"] == 1
    assert result["compatibility"] == 0.82
    assert result["gaps_count"] == 2
    assert result["critical_gaps"] == 1
    assert result["high_gaps"] == 1

    assert len(repository.saved_gaps) == 2


def test_analyze_goal_not_found() -> None:
    """Unknown goal should return empty dict."""

    service = GapAnalysisService(
        repository=FakeCareerRepository(),
        rule_engine=FakeRuleEngine(),
    )

    assert service.analyze_goal(999, {}) == {}


def test_get_learning_path() -> None:
    """Should return learning path."""

    repository = FakeCareerRepository()

    repository.saved_gaps = [
        SimpleNamespace(
            skill_name="Python",
            current_level=2,
            required_level=4,
            gap_severity="critical",
            estimated_hours=40,
        ),
    ]

    service = GapAnalysisService(
        repository=repository,
        rule_engine=FakeRuleEngine(),
    )

    path = service.get_learning_path(1)

    assert len(path) == 1
    assert path[0]["skill"] == "Python"


def test_estimate_timeline_empty() -> None:
    """Empty gaps should return zero estimates."""

    service = GapAnalysisService(
        repository=FakeCareerRepository(),
        rule_engine=FakeRuleEngine(),
    )

    timeline = service.estimate_timeline(1)

    assert timeline["estimated_days"] == 0
    assert timeline["estimated_weeks"] == 0
    assert timeline["estimated_months"] == 0