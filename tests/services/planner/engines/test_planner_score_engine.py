"""Tests for PlannerScoreEngine."""

from __future__ import annotations

from dataclasses import dataclass

from acd.services.planner.engines.planner_score_engine import (
    PlannerScoreEngine,
)


@dataclass
class FakeAnalysis:
    """Simple analysis object for testing."""

    score: float
    weight: float


def test_empty_analysis_returns_zero() -> None:
    """Empty analyses should return zero."""

    engine = PlannerScoreEngine()

    assert engine.calculate_overall_score([]) == 0.0


def test_zero_total_weight_returns_zero() -> None:
    """Total weight equal to zero should return zero."""

    engine = PlannerScoreEngine()

    analyses = [
        FakeAnalysis(score=80, weight=0),
        FakeAnalysis(score=95, weight=0),
    ]

    assert engine.calculate_overall_score(analyses) == 0.0


def test_single_analysis() -> None:
    """Single analysis should return its own score."""

    engine = PlannerScoreEngine()

    analyses = [
        FakeAnalysis(score=87.5, weight=1),
    ]

    assert engine.calculate_overall_score(analyses) == 87.5


def test_weighted_average() -> None:
    """Should calculate weighted average."""

    engine = PlannerScoreEngine()

    analyses = [
        FakeAnalysis(score=80, weight=2),
        FakeAnalysis(score=100, weight=1),
    ]

    assert engine.calculate_overall_score(analyses) == 86.67


def test_equal_weights() -> None:
    """Equal weights should calculate arithmetic mean."""

    engine = PlannerScoreEngine()

    analyses = [
        FakeAnalysis(score=70, weight=1),
        FakeAnalysis(score=80, weight=1),
        FakeAnalysis(score=90, weight=1),
    ]

    assert engine.calculate_overall_score(analyses) == 80.0


def test_rounding_to_two_decimals() -> None:
    """Result should be rounded to two decimal places."""

    engine = PlannerScoreEngine()

    analyses = [
        FakeAnalysis(score=10, weight=1),
        FakeAnalysis(score=11, weight=2),
    ]

    result = engine.calculate_overall_score(analyses)

    assert result == round(result, 2)


def test_high_weights() -> None:
    """Large weights should still produce correct result."""

    engine = PlannerScoreEngine()

    analyses = [
        FakeAnalysis(score=60, weight=100),
        FakeAnalysis(score=90, weight=300),
    ]

    assert engine.calculate_overall_score(analyses) == 82.5