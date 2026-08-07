"""Tests for KnowledgeReuseService."""

from __future__ import annotations

from types import SimpleNamespace

from acd.services.learning.knowledge_reuse_service import (
    KnowledgeReuseService,
)


class FakeRepository:
    """Fake repository."""

    def __init__(self) -> None:
        self.insights = []

    def list_insights(self, **kwargs):
        return self.insights

    def mark_insight_applied(self, insight_id: int):
        return True


def create_service() -> KnowledgeReuseService:
    """Create service using fake repository."""

    service = KnowledgeReuseService.__new__(KnowledgeReuseService)
    service.repository = FakeRepository()
    return service


def create_insight(
    *,
    insight_id: int = 1,
    title: str = "Insight",
    description: str = "Description",
    insight_type: str = "SKILL_RECOMMENDATION",
    confidence: float = 0.9,
    expected_impact: str = "Could improve +20%",
    recommendations: list | None = None,
    is_applied: bool = False,
):
    """Create fake insight."""

    return SimpleNamespace(
        id=insight_id,
        title=title,
        description=description,
        insight_type=insight_type,
        confidence=confidence,
        expected_impact=expected_impact,
        recommendations=recommendations or [],
        is_applied=is_applied,
    )


# ==========================================================
# get_applicable_insights
# ==========================================================


def test_get_applicable_insights() -> None:
    """Should return formatted insights."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            recommendations=[
                {"action": "Python"},
            ]
        )
    )

    result = service.get_applicable_insights()

    assert len(result) == 1
    assert result[0]["title"] == "Insight"


def test_get_applicable_insights_with_context() -> None:
    """Should filter using context."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            recommendations=[
                {"action": "Python"},
            ]
        )
    )

    result = service.get_applicable_insights(
        context={
            "skill": "python",
        }
    )

    assert len(result) == 1


def test_get_applicable_insights_respects_limit() -> None:
    """Should stop when limit is reached."""

    service = create_service()

    service.repository.insights.extend(
        [
            create_insight(insight_id=1),
            create_insight(insight_id=2),
        ]
    )

    result = service.get_applicable_insights(limit=1)

    assert len(result) == 1
    assert result[0]["id"] == 1


# ==========================================================
# get_skill_recommendations
# ==========================================================


def test_get_skill_recommendations() -> None:
    """Should extract skills."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            recommendations=[
                {
                    "action": "Emphasize Python",
                    "rationale": "High demand",
                    "expected_benefit": "Better ATS",
                }
            ]
        )
    )

    result = service.get_skill_recommendations()

    assert result[0]["skill"] == "Python"


def test_get_skill_recommendations_ignores_other_types() -> None:
    """Should ignore non skill recommendation insights."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            insight_type="PLATFORM_ADVICE",
            recommendations=[
                {
                    "action": "LinkedIn",
                    "rationale": "Best",
                    "expected_benefit": "70%",
                }
            ],
        )
    )

    result = service.get_skill_recommendations(
        current_skills=[
            "Python",
        ]
    )

    assert result == []


# ==========================================================
# get_platform_recommendations
# ==========================================================


def test_get_platform_recommendations() -> None:
    """Should extract platform advice."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            insight_type="PLATFORM_ADVICE",
            recommendations=[
                {
                    "action": "LinkedIn",
                    "rationale": "Best",
                    "expected_benefit": "70%",
                }
            ],
        )
    )

    result = service.get_platform_recommendations()

    assert result[0]["platform"] == "LinkedIn"


def test_get_platform_recommendations_ignores_other_types() -> None:
    """Should ignore non platform insights."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            insight_type="TIMING_INSIGHT",
            recommendations=[
                {
                    "action": "Morning",
                    "rationale": "Higher response",
                }
            ],
        )
    )

    assert service.get_platform_recommendations() == []


# ==========================================================
# get_timing_recommendations
# ==========================================================


def test_get_timing_recommendations() -> None:
    """Should collect timing advice."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            insight_type="TIMING_INSIGHT",
            recommendations=[
                {
                    "action": "Morning",
                    "rationale": "Higher response",
                }
            ],
        )
    )

    result = service.get_timing_recommendations()

    assert len(result["recommendations"]) == 1


def test_get_timing_recommendations_ignores_other_types() -> None:
    """Should ignore non timing insights."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            insight_type="LETTER_IMPROVEMENT",
            recommendations=[
                {
                    "action": "Mention leadership",
                    "rationale": "Relevant",
                }
            ],
        )
    )

    result = service.get_timing_recommendations()

    assert result == {
        "best_day": None,
        "best_time": None,
        "recommendations": [],
    }


# ==========================================================
# get_letter_improvements
# ==========================================================


def test_get_letter_improvements() -> None:
    """Should collect improvements."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            insight_type="LETTER_IMPROVEMENT",
            recommendations=[
                {
                    "action": "Mention leadership",
                    "rationale": "Relevant",
                    "expected_benefit": "More interviews",
                }
            ],
        )
    )

    result = service.get_letter_improvements()

    assert result[0]["improvement"] == "Mention leadership"


def test_get_letter_improvements_ignores_other_types() -> None:
    """Should ignore non letter insights."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            insight_type="SECTOR_STRATEGY",
            recommendations=[
                {
                    "action": "Focus cloud",
                    "rationale": "Demand",
                    "expected_benefit": "Higher success",
                }
            ],
        )
    )

    assert service.get_letter_improvements() == []


# ==========================================================
# get_sector_strategy
# ==========================================================


def test_get_sector_strategy() -> None:
    """Should return sector strategy."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            insight_type="SECTOR_STRATEGY",
            description="Technology sector",
            recommendations=[
                {
                    "action": "Focus cloud",
                    "rationale": "Demand",
                    "expected_benefit": "Higher success",
                }
            ],
        )
    )

    result = service.get_sector_strategy("technology")

    assert len(result) == 1
    assert result[0]["sector"] == "technology"


def test_get_sector_strategy_without_sector() -> None:
    """Should accept general sector strategy."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            insight_type="SECTOR_STRATEGY",
            description="General strategy",
            recommendations=[
                {
                    "action": "Focus cloud",
                    "rationale": "Demand",
                    "expected_benefit": "Higher success",
                }
            ],
        )
    )

    result = service.get_sector_strategy()

    assert len(result) == 1
    assert result[0]["sector"] == "General"


# ==========================================================
# apply_insight
# ==========================================================


def test_apply_insight() -> None:
    """Should mark insight as applied."""

    service = create_service()

    result = service.apply_insight(10)

    assert result["success"] is True
    assert result["insight_id"] == 10
    assert result["applied_at"] is not None


def test_apply_insight_failure() -> None:
    """Should return no applied_at when marking fails."""

    service = create_service()
    service.repository.mark_insight_applied = lambda insight_id: False

    result = service.apply_insight(10)

    assert result["success"] is False
    assert result["insight_id"] == 10
    assert result["applied_at"] is None


# ==========================================================
# get_knowledge_impact
# ==========================================================


def test_get_knowledge_impact() -> None:
    """Should calculate impact."""

    service = create_service()

    service.repository.insights.extend(
        [
            create_insight(
                confidence=0.8,
                is_applied=True,
                expected_impact="Could improve +10%",
            ),
            create_insight(
                confidence=1.0,
                is_applied=True,
                expected_impact="Could improve +20%",
            ),
        ]
    )

    result = service.get_knowledge_impact()

    assert result["total_applied_insights"] == 2
    assert result["average_confidence"] == 0.9
    assert result["estimated_improvement"] == 15.0


def test_get_knowledge_impact_ignores_invalid_expected_impact() -> None:
    """Should ignore malformed improvement text."""

    service = create_service()

    service.repository.insights.append(
        create_insight(
            confidence=0.8,
            is_applied=True,
            expected_impact="Could improve significantly",
        )
    )

    result = service.get_knowledge_impact()

    assert result["total_applied_insights"] == 1
    assert result["average_confidence"] == 0.8
    assert result["estimated_improvement"] == 0.0


# ==========================================================
# private helpers
# ==========================================================


def test_format_insight() -> None:
    """Should format insight."""

    service = create_service()

    insight = create_insight()

    result = service._format_insight(insight)

    assert result["id"] == 1
    assert result["title"] == "Insight"


def test_insight_matches_context() -> None:
    """Should match context."""

    service = create_service()

    insight = create_insight(
        recommendations=[
            {
                "action": "Python",
            }
        ]
    )

    assert service._insight_matches_context(
        insight,
        {
            "skill": "python",
        },
    )


def test_insight_matches_context_with_list() -> None:
    """Should match when context contains list values."""

    service = create_service()

    insight = create_insight(
        recommendations=[
            {
                "action": "Python",
            }
        ]
    )

    assert service._insight_matches_context(
        insight,
        {
            "skills": [
                "sql",
                "python",
            ],
        },
    )