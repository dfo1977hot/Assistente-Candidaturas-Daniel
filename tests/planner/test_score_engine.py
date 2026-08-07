from acd.domain.planner.analysis import Analysis
from acd.services.planner import PlannerScoreEngine


def test_weighted_average():
    engine = PlannerScoreEngine()

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

    score = engine.calculate_overall_score(analyses)

    assert score == 90.0


def test_empty_analysis_returns_zero():
    engine = PlannerScoreEngine()

    assert engine.calculate_overall_score([]) == 0.0


def test_zero_weight_returns_zero():
    engine = PlannerScoreEngine()

    analyses = [
        Analysis("ATS", 90, 0.0),
        Analysis("Mercado", 100, 0.0),
    ]

    assert engine.calculate_overall_score(analyses) == 0.0


def test_rounding():
    engine = PlannerScoreEngine()

    analyses = [
        Analysis("A", 91, 0.5),
        Analysis("B", 88, 0.5),
    ]

    assert engine.calculate_overall_score(analyses) == 89.5
