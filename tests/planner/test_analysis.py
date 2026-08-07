from acd.domain.planner.analysis import Analysis


def test_analysis_creation():

    analysis = Analysis(
        name="ATS",
        score=91,
        weight=0.35,
        observation="Excelente aderência",
    )

    assert analysis.name == "ATS"

    assert analysis.score == 91

    assert analysis.weight == 0.35

    assert analysis.observation == "Excelente aderência"
