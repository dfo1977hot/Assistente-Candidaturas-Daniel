from acd.domain.planner import Analysis
from acd.services.planner import PlannerService


def test_plan_returns_result():

    service = PlannerService()

    analyses = [
        Analysis(
            name="ATS",
            score=90,
            weight=0.40,
        ),
        Analysis(
            name="Experiência",
            score=80,
            weight=0.30,
        ),
        Analysis(
            name="Mercado",
            score=100,
            weight=0.30,
        ),
    ]

    result = service.plan(analyses)

    assert result.overall_score == 90.0

    assert len(result.recommendations) == 1

    assert result.recommendations[0].title == "Aplicar imediatamente"
