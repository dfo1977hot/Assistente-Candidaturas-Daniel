"""Tests for CareerSimulationService."""

from __future__ import annotations

from acd.services.career_simulation_service import CareerSimulationService


class FakeRuleEngine:
    """Fake rule engine."""

    def analyze_compatibility(self, profile, target_role):
        score = 50.0

        score += sum(profile.get("skills", {}).values())

        score += len(profile.get("certifications", [])) * 5

        return {
            "compatibility": score,
        }


def create_service() -> CareerSimulationService:
    """Create service with fake rule engine."""

    return CareerSimulationService(
        rule_engine=FakeRuleEngine(),
    )


def test_simulate_skill_improvement() -> None:
    """Should simulate improving one skill."""

    service = create_service()

    profile = {
        "skills": {
            "Python": 3,
        }
    }

    result = service.simulate_skill_improvement(
        profile,
        "Manager",
        "Python",
        2,
    )

    assert result["skill"] == "Python"
    assert result["from_level"] == 3
    assert result["to_level"] == 5
    assert result["simulated_compatibility"] > result["current_compatibility"]


def test_skill_level_is_capped_at_ten() -> None:
    """Skill level cannot exceed ten."""

    service = create_service()

    profile = {
        "skills": {
            "Python": 9,
        }
    }

    result = service.simulate_skill_improvement(
        profile,
        "Manager",
        "Python",
        5,
    )

    assert result["to_level"] == 10


def test_simulate_certification() -> None:
    """Should simulate obtaining certification."""

    service = create_service()

    result = service.simulate_certification(
        {},
        "Manager",
        "PMP",
    )

    assert result["certification"] == "PMP"
    assert result["simulated_compatibility"] > result["current_compatibility"]


def test_simulate_multiple_improvements() -> None:
    """Should simulate multiple improvements."""

    service = create_service()

    result = service.simulate_multiple_improvements(
        {},
        "Manager",
        {
            "skills": {
                "Python": 5,
                "Power BI": 4,
            },
            "certifications": [
                "PMP",
            ],
        },
    )

    assert result["improvements_applied"]["skills"] == [
        "Python",
        "Power BI",
    ]

    assert result["improvements_applied"]["certifications"] == [
        "PMP",
    ]


def test_compare_scenarios() -> None:
    """Should rank scenarios."""

    service = create_service()

    scenarios = [
        {
            "name": "Scenario A",
            "skills": {
                "Python": 2,
            },
        },
        {
            "name": "Scenario B",
            "skills": {
                "Python": 8,
            },
        },
    ]

    results = service.compare_scenarios(
        {},
        "Manager",
        scenarios,
    )

    assert len(results) == 2
    assert results[0]["name"] == "Scenario B"
    assert results[1]["name"] == "Scenario A"


def test_what_if_certification() -> None:
    """Should detect certification query."""

    service = create_service()

    result = service.what_if_query(
        "Se eu obtiver uma certificação PMP?",
        {},
        "Manager",
    )

    assert "certification" in result


def test_what_if_skill() -> None:
    """Should detect skill improvement query."""

    service = create_service()

    result = service.what_if_query(
        "Se eu melhorar meu inglês?",
        {},
        "Manager",
    )

    assert result["skill"] == "Skill Extraída"


def test_what_if_experience() -> None:
    """Should detect experience query."""

    service = create_service()

    result = service.what_if_query(
        "Se eu ganhar experiência em logística?",
        {},
        "Manager",
    )

    assert result["skill"] == "Experiência"


def test_what_if_unknown_query() -> None:
    """Should return default response."""

    service = create_service()

    result = service.what_if_query(
        "Qual é a previsão do tempo?",
        {},
        "Manager",
    )

    assert "response" in result