from __future__ import annotations

from acd.application.planner import PlannerFacade
from acd.domain.planner import Analysis
from acd.services.planner import PlannerService


def test_planner_facade_returns_result() -> None:
    """PlannerFacade delegates planning to PlannerService."""

    facade = PlannerFacade(
        PlannerService(),
    )

    result = facade.analyze(
        [
            Analysis(
                name="Compatibilidade da vaga",
                score=80.0,
                weight=1.0,
            )
        ]
    )

    assert result is not None

    assert result.overall_score >= 0