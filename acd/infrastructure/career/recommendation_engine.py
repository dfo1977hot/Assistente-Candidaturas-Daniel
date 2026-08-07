from __future__ import annotations

from typing import Any

from acd.infrastructure.career.rule_engine import CareerRuleEngine


class RecommendationRankingEngine:
    """Engine for generating and ranking career recommendations."""

    RECOMMENDATION_TEMPLATES = {
        "skills": [
            {
                "title": "Aprimorar {skill}",
                "description": "Desenvolver competência em {skill} através de cursos online ou treinamentos práticos",
                "impact": 7,
                "effort": 6,
                "duration_days": 60,
                "category": "skills",
            },
        ],
        "certifications": [
            {
                "title": "Obter certificação {cert}",
                "description": "Realizar e passar no exame de certificação {cert}",
                "impact": 8,
                "effort": 7,
                "duration_days": 120,
                "category": "certifications",
            },
        ],
        "languages": [
            {
                "title": "Melhorar {language} para nível {level}",
                "description": "Investir em cursos de idioma e prática para atingir nível {level}",
                "impact": 6,
                "effort": 8,
                "duration_days": 180,
                "category": "languages",
            },
        ],
        "experience": [
            {
                "title": "Buscar experiência em {domain}",
                "description": "Procurar projetos internos ou externos para ganhar experiência em {domain}",
                "impact": 9,
                "effort": 7,
                "duration_days": 90,
                "category": "experience",
            },
        ],
        "resume": [
            {
                "title": "Revisar e otimizar currículo",
                "description": "Atualizar currículo destacando experiências relevantes para {role}",
                "impact": 6,
                "effort": 3,
                "duration_days": 7,
                "category": "resume",
            },
        ],
        "networking": [
            {
                "title": "Expandir rede profissional em {industry}",
                "description": "Participar de eventos, conferências e grupos profissionais em {industry}",
                "impact": 7,
                "effort": 5,
                "duration_days": 60,
                "category": "networking",
            },
        ],
    }

    def __init__(self, rule_engine: CareerRuleEngine | None = None) -> None:
        self.rule_engine = rule_engine or CareerRuleEngine()

    def generate_recommendations(
        self, goal_data: dict[str, Any], gaps: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate recommendations based on goal and gaps.

        Args:
            goal_data: Career goal data
            gaps: List of skill gaps

        Returns:
            List of recommendations ordered by priority
        """
        recommendations = []

        # 1. Skill gap recommendations
        for gap in gaps:
            if gap["severity"] in ["critical", "high"]:
                rec = {
                    "title": f"Aprimorar {gap['skill']}",
                    "description": f"Desenvolver competência em {gap['skill']} do nível {gap['current']} para {gap['required']}",
                    "impact": min(10, (gap["required"] - gap["current"]) * 1.5),
                    "effort": min(10, (gap["required"] - gap["current"]) * 1.2),
                    "duration_days": gap.get("estimated_hours", 40) // 8,
                    "category": "skills",
                    "target": gap["skill"],
                }
                recommendations.append(rec)

        # 2. Certification recommendations
        target_role = goal_data.get("target_role", "")
        if target_role in self.rule_engine.ROLE_COMPETENCIES:
            certs = self.rule_engine.ROLE_COMPETENCIES[target_role].get(
                "desired_certifications", []
            )
            for cert in certs[:3]:  # Top 3 certifications
                rec = {
                    "title": f"Obter certificação {cert}",
                    "description": f"Realizar treinamento e exame de certificação {cert}",
                    "impact": 8,
                    "effort": 7,
                    "duration_days": 120,
                    "category": "certifications",
                    "target": cert,
                }
                recommendations.append(rec)

        # 3. Language recommendations
        if goal_data.get("target_industry", ""):
            rec = {
                "title": "Aprimorar Inglês",
                "description": "Atingir nível C1 em Inglês para melhor competitividade internacional",
                "impact": 6,
                "effort": 8,
                "duration_days": 180,
                "category": "languages",
                "target": "Inglês",
            }
            recommendations.append(rec)

        # 4. Resume optimization
        rec = {
            "title": "Otimizar currículo",
            "description": f"Revisar e destacar experiências relevantes para {target_role}",
            "impact": 6,
            "effort": 3,
            "duration_days": 7,
            "category": "resume",
            "target": "currículo",
        }
        recommendations.append(rec)

        # 5. Networking
        rec = {
            "title": f"Expandir networking em {goal_data.get('target_industry', 'sua área')}",
            "description": "Participar de eventos profissionais e grupos de discussão",
            "impact": 7,
            "effort": 5,
            "duration_days": 60,
            "category": "networking",
            "target": goal_data.get("target_industry", ""),
        }
        recommendations.append(rec)

        # Rank all recommendations
        ranked = self.rule_engine.rank_recommendations(recommendations)
        return ranked

    def get_quick_wins(
        self, recommendations: list[dict[str, Any]], max_effort: float = 3.0
    ) -> list[dict[str, Any]]:
        """Get quick wins: high impact, low effort recommendations."""
        return [r for r in recommendations if r["effort"] <= max_effort and r["impact"] >= 5]

    def simulate_scenario(
        self,
        current_compatibility: float,
        recommendations_to_implement: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Simulate impact of implementing specific recommendations.

        Args:
            current_compatibility: Current compatibility score
            recommendations_to_implement: List of recommendations to simulate

        Returns:
            Simulated compatibility and timeline
        """
        total_impact = 0
        total_duration = 0
        implemented = []

        for rec in recommendations_to_implement:
            # Each point of impact adds ~2% to compatibility
            impact_percent = (rec.get("impact", 5) / 10) * 8  # Scale to 0-8%
            total_impact += impact_percent
            total_duration = max(total_duration, rec.get("duration_days", 30))
            implemented.append(rec["title"])

        new_compatibility = min(100, current_compatibility + total_impact)

        return {
            "current_compatibility": round(current_compatibility, 1),
            "projected_compatibility": round(new_compatibility, 1),
            "improvement": round(new_compatibility - current_compatibility, 1),
            "estimated_timeline_days": total_duration,
            "recommendations": implemented,
        }
