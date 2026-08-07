from acd.domain.planner.enums import (
    PriorityLevel,
    StrategyType,
)


def test_priority_values():
    assert PriorityLevel.HIGH.value == "high"


def test_strategy_values():
    assert StrategyType.APPLY_NOW.value == "apply_now"
