"""Tests for RecommendationEngine."""

from __future__ import annotations

from acd.services.planner.engines.recommendation_engine import (
    RecommendationEngine,
)


def test_generate_high_score() -> None:
    """High scores should recommend immediate application."""

    engine = RecommendationEngine()

    recommendations = engine.generate(95)

    assert len(recommendations) == 1

    recommendation = recommendations[0]

    assert recommendation.title == "Aplicar imediatamente"
    assert recommendation.description == (
        "A vaga possui excelente aderência."
    )


def test_generate_boundary_high_score() -> None:
    """Score 90 should still be considered excellent."""

    engine = RecommendationEngine()

    recommendations = engine.generate(90)

    assert recommendations[0].title == "Aplicar imediatamente"


def test_generate_medium_score() -> None:
    """Medium scores should recommend adapting the resume."""

    engine = RecommendationEngine()

    recommendations = engine.generate(80)

    recommendation = recommendations[0]

    assert recommendation.title == "Adaptar currículo"
    assert recommendation.description == (
        "Pequenos ajustes podem aumentar a aderência."
    )


def test_generate_boundary_medium_score() -> None:
    """Score 75 should enter medium range."""

    engine = RecommendationEngine()

    recommendations = engine.generate(75)

    assert recommendations[0].title == "Adaptar currículo"


def test_generate_low_score() -> None:
    """Low scores should recommend low priority."""

    engine = RecommendationEngine()

    recommendations = engine.generate(60)

    recommendation = recommendations[0]

    assert recommendation.title == "Baixa prioridade"
    assert recommendation.description == (
        "Considere investir seu tempo em outras vagas."
    )


def test_generate_boundary_low_score() -> None:
    """Score below 75 should be low priority."""

    engine = RecommendationEngine()

    recommendations = engine.generate(74.99)

    assert recommendations[0].title == "Baixa prioridade"


def test_generate_returns_recommendation_list() -> None:
    """Engine should always return a list with one recommendation."""

    engine = RecommendationEngine()

    for score in (0, 40, 75, 90, 100):
        recommendations = engine.generate(score)

        assert isinstance(recommendations, list)
        assert len(recommendations) == 1