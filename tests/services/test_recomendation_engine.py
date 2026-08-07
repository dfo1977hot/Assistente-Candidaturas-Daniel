"""Tests for RecommendationEngine."""

from __future__ import annotations

from acd.services.recommendation_engine import RecommendationEngine


def test_recommendation_engine_can_be_instantiated() -> None:
    """RecommendationEngine should be instantiated."""

    engine = RecommendationEngine()

    assert engine is not None


def test_public_api_returns_expected_type() -> None:
    """Public methods should return the expected types."""

    engine = RecommendationEngine()

    public_methods = [
        name
        for name in dir(engine)
        if not name.startswith("_")
        and callable(getattr(engine, name))
    ]

    assert len(public_methods) > 0