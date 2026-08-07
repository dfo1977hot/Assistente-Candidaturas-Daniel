from acd.domain.planner import PlannerResult
from acd.domain.planner.priority import Priority


def test_default_values():

    result = PlannerResult()

    assert result.overall_score == 0

    assert result.priority == Priority.NORMAL

    assert result.followup_days == 7

    assert result.missing_keywords == []

    assert result.recommendations == []

    assert result.warnings == []
