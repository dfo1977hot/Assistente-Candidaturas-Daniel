from acd.application.planner import PlannerFacade
from acd.domain.planner import Analysis


def test_facade_returns_planner_result():

    facade = PlannerFacade()

    analyses = [
        Analysis(
            name="ATS",
            score=90,
            weight=1.0,
        )
    ]

    result = facade.analyze(analyses)

    assert result.overall_score == 90.0
