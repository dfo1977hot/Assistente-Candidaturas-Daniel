"""Tests for PlannerService."""

from __future__ import annotations

from dataclasses import dataclass

from acd.domain.planner.enums import StrategyType
from acd.services.planner.planner_service import PlannerService


@dataclass
class FakeAnalysis:
    """Simple analysis object."""

    score: float
    weight: float


def test_plan_high_score() -> None:
    """High scores should generate APPLY_NOW strategy."""

    service = PlannerService()

    analyses = [
        FakeAnalysis(score=95.0, weight=1),
        FakeAnalysis(score=90.0, weight=1),
    ]

    result = service.plan(analyses)

    assert result.overall_score == 92.5

    assert result.strategy is StrategyType.APPLY_NOW

    assert len(result.recommendations) == 1
    assert result.recommendations[0].title == "Aplicar imediatamente"


def test_plan_medium_score() -> None:
    """Medium scores should recommend adapting the resume."""

    service = PlannerService()

    analyses = [
        FakeAnalysis(score=80.0, weight=1),
        FakeAnalysis(score=76.0, weight=1),
    ]

    result = service.plan(analyses)

    assert result.overall_score == 78.0

    assert result.strategy is StrategyType.ADAPT_RESUME

    assert result.recommendations[0].title == "Adaptar currículo"


def test_plan_resume_and_cover() -> None:
    """Intermediate scores should adapt resume and cover."""

    service = PlannerService()

    analyses = [
        FakeAnalysis(score=60.0, weight=1),
        FakeAnalysis(score=65.0, weight=1),
    ]

    result = service.plan(analyses)

    assert result.overall_score == 62.5

    assert (
        result.strategy
        is StrategyType.ADAPT_RESUME_AND_COVER
    )

    assert result.recommendations[0].title == "Baixa prioridade"


def test_plan_low_priority() -> None:
    """Low scores should produce low priority."""

    service = PlannerService()

    analyses = [
        FakeAnalysis(score=30.0, weight=1),
        FakeAnalysis(score=40.0, weight=1),
    ]

    result = service.plan(analyses)

    assert result.overall_score == 35.0

    assert result.strategy is StrategyType.LOW_PRIORITY

    assert result.recommendations[0].title == "Baixa prioridade"


def test_plan_empty_analysis() -> None:
    """Empty analyses should produce zero score."""

    service = PlannerService()

    result = service.plan([])

    assert result.overall_score == 0.0

    assert result.strategy is StrategyType.LOW_PRIORITY

    assert len(result.recommendations) == 1


def test_plan_returns_planner_result() -> None:
    """Planner should always populate PlannerResult."""

    service = PlannerService()

    result = service.plan([])

    assert hasattr(result, "overall_score")
    assert hasattr(result, "recommendations")
    assert hasattr(result, "strategy")