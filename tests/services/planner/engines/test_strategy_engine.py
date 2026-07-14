"""Tests for StrategyEngine."""

from __future__ import annotations

from acd.domain.planner.enums import StrategyType
from acd.services.planner.engines.strategy_engine import StrategyEngine


def test_apply_now() -> None:
    """Scores >= 90 should apply immediately."""

    engine = StrategyEngine()

    assert engine.determine(95) is StrategyType.APPLY_NOW


def test_apply_now_boundary() -> None:
    """Score 90 belongs to APPLY_NOW."""

    engine = StrategyEngine()

    assert engine.determine(90) is StrategyType.APPLY_NOW


def test_adapt_resume() -> None:
    """Scores between 75 and 89.99 should adapt resume."""

    engine = StrategyEngine()

    assert engine.determine(80) is StrategyType.ADAPT_RESUME


def test_adapt_resume_boundary() -> None:
    """Score 75 belongs to ADAPT_RESUME."""

    engine = StrategyEngine()

    assert engine.determine(75) is StrategyType.ADAPT_RESUME


def test_adapt_resume_and_cover() -> None:
    """Scores between 60 and 74.99 should adapt resume and cover."""

    engine = StrategyEngine()

    assert (
        engine.determine(65)
        is StrategyType.ADAPT_RESUME_AND_COVER
    )


def test_adapt_resume_and_cover_boundary() -> None:
    """Score 60 belongs to ADAPT_RESUME_AND_COVER."""

    engine = StrategyEngine()

    assert (
        engine.determine(60)
        is StrategyType.ADAPT_RESUME_AND_COVER
    )


def test_low_priority() -> None:
    """Scores below 60 should be low priority."""

    engine = StrategyEngine()

    assert engine.determine(40) is StrategyType.LOW_PRIORITY


def test_low_priority_boundary() -> None:
    """Score just below 60 should be low priority."""

    engine = StrategyEngine()

    assert engine.determine(59.99) is StrategyType.LOW_PRIORITY


def test_all_strategies_are_reachable() -> None:
    """Every strategy should be reachable."""

    engine = StrategyEngine()

    strategies = {
        engine.determine(95),
        engine.determine(80),
        engine.determine(65),
        engine.determine(20),
    }

    assert strategies == {
        StrategyType.APPLY_NOW,
        StrategyType.ADAPT_RESUME,
        StrategyType.ADAPT_RESUME_AND_COVER,
        StrategyType.LOW_PRIORITY,
    }