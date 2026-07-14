"""Tests for RecommendationEngine."""

from __future__ import annotations

from acd.services.recommendation_engine import RecommendationEngine


class FakeMetricsEngine:
    """Fake metrics engine for deterministic tests."""

    def __init__(self, metrics: dict) -> None:
        self._metrics = metrics

    def calculate_all_metrics(self) -> dict:
        return self._metrics


class FakeRepository:
    """Fake repository for persistence tests."""

    def __init__(self) -> None:
        self.saved: list[dict] = []

    def create_recommendation(
        self,
        title: str,
        description: str,
        priority: str,
        action: str,
    ) -> None:
        self.saved.append(
            {
                "title": title,
                "description": description,
                "priority": priority,
                "action": action,
            }
        )


def test_generate_recommendations_all_rules() -> None:
    """Should generate every applicable recommendation."""

    metrics = {
        "ats": {
            "average_ats": 60,
        },
        "conversion": {
            "conversion_interview_rate": 0.10,
        },
        "platforms": {
            "best_platform": "workday",
        },
        "time": {
            "avg_time_to_response": 8,
        },
    }

    engine = RecommendationEngine(
        repository=FakeRepository(),
        metrics_engine=FakeMetricsEngine(metrics),
    )

    recommendations = engine.generate_recommendations()

    assert len(recommendations) == 4

    actions = {r["action"] for r in recommendations}

    assert "review_curriculum" in actions
    assert "increase_applications" in actions
    assert "prioritize_platform" in actions
    assert "followup_applications" in actions


def test_generate_recommendations_no_rules() -> None:
    """Should generate no recommendations."""

    metrics = {
        "ats": {
            "average_ats": 90,
        },
        "conversion": {
            "conversion_interview_rate": 0.30,
        },
        "platforms": {
            "best_platform": "linkedin",
        },
        "time": {
            "avg_time_to_response": 2,
        },
    }

    engine = RecommendationEngine(
        repository=FakeRepository(),
        metrics_engine=FakeMetricsEngine(metrics),
    )

    assert engine.generate_recommendations() == []


def test_save_recommendations() -> None:
    """Should persist generated recommendations."""

    repository = FakeRepository()

    metrics = {
        "ats": {
            "average_ats": 60,
        },
        "conversion": {
            "conversion_interview_rate": 0.10,
        },
        "platforms": {
            "best_platform": "workday",
        },
        "time": {
            "avg_time_to_response": 8,
        },
    }

    engine = RecommendationEngine(
        repository=repository,
        metrics_engine=FakeMetricsEngine(metrics),
    )

    engine.save_recommendations()

    assert len(repository.saved) == 4

    assert repository.saved[0]["title"] == "Revisar formato do currículo"

    actions = {item["action"] for item in repository.saved}

    assert actions == {
        "review_curriculum",
        "increase_applications",
        "prioritize_platform",
        "followup_applications",
    }