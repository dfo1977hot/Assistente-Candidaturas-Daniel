from __future__ import annotations

from copy import deepcopy
from typing import Any

from acd.infrastructure.career.recommendation_engine import RecommendationRankingEngine
from acd.infrastructure.career.rule_engine import CareerRuleEngine


class CareerSimulationService:
    """Service for simulating career development scenarios without modifying real data."""

    def __init__(
        self,
        rule_engine: CareerRuleEngine | None = None,
        recommendation_engine: RecommendationRankingEngine | None = None,
    ) -> None:
        self.rule_engine = rule_engine or CareerRuleEngine()
        self.recommendation_engine = recommendation_engine or RecommendationRankingEngine(
            self.rule_engine
        )

    def simulate_skill_improvement(
        self,
        current_profile: dict[str, Any],
        target_role: str,
        skill_name: str,
        improvement_levels: int,
    ) -> dict[str, Any]:
        """Simulate improving a specific skill."""

        current_analysis = self.rule_engine.analyze_compatibility(
            current_profile,
            target_role,
        )

        simulated_profile = deepcopy(current_profile)

        if "skills" not in simulated_profile:
            simulated_profile["skills"] = {}

        current_level = simulated_profile["skills"].get(skill_name, 0)
        simulated_profile["skills"][skill_name] = min(
            10,
            current_level + improvement_levels,
        )

        simulated_analysis = self.rule_engine.analyze_compatibility(
            simulated_profile,
            target_role,
        )

        return {
            "scenario": f"Melhorar {skill_name} em {improvement_levels} níveis",
            "current_compatibility": round(current_analysis["compatibility"], 1),
            "simulated_compatibility": round(simulated_analysis["compatibility"], 1),
            "improvement": round(
                simulated_analysis["compatibility"]
                - current_analysis["compatibility"],
                1,
            ),
            "skill": skill_name,
            "from_level": current_level,
            "to_level": min(10, current_level + improvement_levels),
        }

    def simulate_certification(
        self,
        current_profile: dict[str, Any],
        target_role: str,
        certification: str,
    ) -> dict[str, Any]:
        """Simulate obtaining a certification."""

        current_analysis = self.rule_engine.analyze_compatibility(
            current_profile,
            target_role,
        )

        simulated_profile = deepcopy(current_profile)

        if "certifications" not in simulated_profile:
            simulated_profile["certifications"] = []

        if certification not in simulated_profile["certifications"]:
            simulated_profile["certifications"].append(certification)

        simulated_analysis = self.rule_engine.analyze_compatibility(
            simulated_profile,
            target_role,
        )

        return {
            "scenario": f"Obter certificação {certification}",
            "current_compatibility": round(current_analysis["compatibility"], 1),
            "simulated_compatibility": round(simulated_analysis["compatibility"], 1),
            "improvement": round(
                simulated_analysis["compatibility"]
                - current_analysis["compatibility"],
                1,
            ),
            "certification": certification,
        }

    def simulate_multiple_improvements(
        self,
        current_profile: dict[str, Any],
        target_role: str,
        improvements: dict[str, Any],
    ) -> dict[str, Any]:
        """Simulate multiple improvements at once."""

        current_analysis = self.rule_engine.analyze_compatibility(
            current_profile,
            target_role,
        )

        simulated_profile = deepcopy(current_profile)

        if "skills" in improvements:
            if "skills" not in simulated_profile:
                simulated_profile["skills"] = {}
            simulated_profile["skills"].update(improvements["skills"])

        if "certifications" in improvements:
            if "certifications" not in simulated_profile:
                simulated_profile["certifications"] = []
            simulated_profile["certifications"].extend(
                improvements["certifications"]
            )

        simulated_analysis = self.rule_engine.analyze_compatibility(
            simulated_profile,
            target_role,
        )

        return {
            "scenario": "Cenário de múltiplas melhorias",
            "current_compatibility": round(current_analysis["compatibility"], 1),
            "simulated_compatibility": round(simulated_analysis["compatibility"], 1),
            "improvement": round(
                simulated_analysis["compatibility"]
                - current_analysis["compatibility"],
                1,
            ),
            "improvements_applied": {
                "skills": list(improvements.get("skills", {}).keys()),
                "certifications": improvements.get("certifications", []),
            },
        }

    def compare_scenarios(
        self,
        current_profile: dict[str, Any],
        target_role: str,
        scenarios: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Compare multiple scenarios to determine best path."""

        results: list[dict[str, Any]] = []

        for scenario in scenarios:
            simulated_profile = deepcopy(current_profile)

            if "skills" in scenario:
                if "skills" not in simulated_profile:
                    simulated_profile["skills"] = {}
                simulated_profile["skills"].update(scenario["skills"])

            if "certifications" in scenario:
                if "certifications" not in simulated_profile:
                    simulated_profile["certifications"] = []
                simulated_profile["certifications"].extend(
                    scenario["certifications"]
                )

            analysis = self.rule_engine.analyze_compatibility(
                simulated_profile,
                target_role,
            )

            results.append(
                {
                    "name": scenario.get("name", "Unnamed scenario"),
                    "compatibility": round(analysis["compatibility"], 1),
                    "improvements": scenario,
                }
            )

        return sorted(
            results,
            key=lambda item: item["compatibility"],
            reverse=True,
        )

    def what_if_query(
        self,
        query: str,
        current_profile: dict[str, Any],
        target_role: str,
    ) -> dict[str, Any]:
        """Answer 'what-if' questions about career development."""

        query_lower = query.lower()

        if "certificação" in query_lower or "certificado" in query_lower:
            return self.simulate_certification(
                current_profile,
                target_role,
                "Certificação Extraída",
            )

        if "melhorar" in query_lower or "aprimorar" in query_lower:
            return self.simulate_skill_improvement(
                current_profile,
                target_role,
                "Skill Extraída",
                3,
            )

        if "experiência" in query_lower:
            return self.simulate_skill_improvement(
                current_profile,
                target_role,
                "Experiência",
                2,
            )

        return {
            "query": query,
            "response": (
                "Não consegui interpretar a pergunta. "
                "Tente formular de forma mais específica."
            ),
        }