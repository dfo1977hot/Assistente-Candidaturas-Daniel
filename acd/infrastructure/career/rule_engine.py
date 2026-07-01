from __future__ import annotations

from typing import Any


class CareerRuleEngine:
    """Deterministic rule engine for career analysis and recommendations."""

    # Role-to-competency mapping
    ROLE_COMPETENCIES = {
        "Coordenador de Supply Chain": {
            "required_skills": [
                ("SAP S/4HANA", 8),
                ("Planejamento de Demanda", 8),
                ("S&OP Avançado", 7),
                ("Lean Manufacturing", 7),
                ("Power BI", 6),
                ("Excel Avançado", 7),
                ("Gestão Logística", 9),
            ],
            "desired_certifications": ["APICS CSCP", "APICS CPIM", "APICS CSCP"],
            "languages": [("Inglês", 7), ("Espanhol", 5)],
        },
        "Gerente de Operações": {
            "required_skills": [
                ("Liderança", 9),
                ("Análise de Dados", 8),
                ("Gestão de Processos", 8),
                ("Power BI", 7),
                ("Six Sigma", 7),
            ],
            "desired_certifications": ["PMP", "ITIL", "Lean Six Sigma"],
            "languages": [("Inglês", 8)],
        },
        "Analista de Dados": {
            "required_skills": [
                ("Python", 8),
                ("SQL", 8),
                ("Power BI", 8),
                ("Análise Estatística", 7),
                ("Visualização de Dados", 7),
            ],
            "desired_certifications": ["Google Data Analytics", "Microsoft Certified"],
            "languages": [("Inglês", 7)],
        },
    }

    def analyze_compatibility(self, current_profile: dict[str, Any], target_role: str) -> dict[str, Any]:
        """Analyze compatibility between current profile and target role.
        
        Args:
            current_profile: Dictionary with current skills, certifications, languages
            target_role: Target position title
            
        Returns:
            Dictionary with compatibility score and gap analysis
        """
        if target_role not in self.ROLE_COMPETENCIES:
            return {"compatibility": 0, "message": f"Cargo '{target_role}' não mapeado no sistema"}

        requirements = self.ROLE_COMPETENCIES[target_role]
        current_skills = current_profile.get("skills", {})
        current_certs = current_profile.get("certifications", [])
        current_langs = current_profile.get("languages", {})

        # Calculate skill compatibility
        total_skill_points = sum(level for _, level in requirements["required_skills"])
        achieved_skill_points = 0

        gaps = []
        for skill_name, required_level in requirements["required_skills"]:
            current_level = current_skills.get(skill_name, 0)
            achieved_skill_points += min(current_level, required_level)

            if current_level < required_level:
                severity = "critical" if required_level - current_level > 5 else "high" if required_level - current_level > 3 else "medium"
                gaps.append({
                    "skill": skill_name,
                    "current": current_level,
                    "required": required_level,
                    "severity": severity,
                })

        skill_compatibility = (achieved_skill_points / total_skill_points * 100) if total_skill_points > 0 else 0

        # Certificate bonus
        cert_bonus = len([c for c in current_certs if c in requirements["desired_certifications"]]) * 5
        cert_bonus = min(cert_bonus, 15)

        # Language bonus
        lang_bonus = 0
        for lang, required_level in requirements["languages"]:
            if current_langs.get(lang, 0) >= required_level * 0.8:
                lang_bonus += 5

        total_compatibility = min(100, skill_compatibility * 0.7 + cert_bonus + lang_bonus)

        return {
            "compatibility": round(total_compatibility, 1),
            "skill_compatibility": round(skill_compatibility, 1),
            "gaps": gaps,
            "strengths": self._identify_strengths(current_skills, requirements["required_skills"]),
            "certificates_missing": [c for c in requirements["desired_certifications"] if c not in current_certs],
        }

    def _identify_strengths(self, current_skills: dict[str, Any], required: list[tuple[str, int]]) -> list[str]:
        """Identify current strengths compared to requirements."""
        strengths = []
        for skill_name, required_level in required:
            current_level = current_skills.get(skill_name, 0)
            if current_level >= required_level:
                strengths.append(skill_name)
        return strengths

    def calculate_priority_score(self, impact: float, effort: float, alignment: float = 1.0) -> float:
        """Calculate priority score for recommendations.
        
        Priority = (Impact * Alignment) / Effort
        
        Args:
            impact: Expected impact (1-10)
            effort: Estimated effort (1-10)
            alignment: Goal alignment factor (0-1)
            
        Returns:
            Priority score for ranking
        """
        if effort == 0:
            effort = 1
        return (impact * alignment) / effort

    def rank_recommendations(self, recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Rank recommendations by priority score."""
        ranked = []
        for idx, rec in enumerate(recommendations, 1):
            priority_score = self.calculate_priority_score(
                rec.get("impact", 5),
                rec.get("effort", 5),
                rec.get("alignment", 1.0),
            )
            rec["priority_score"] = round(priority_score, 2)
            rec["rank"] = idx
            ranked.append(rec)

        return sorted(ranked, key=lambda x: x["priority_score"], reverse=True)

    def generate_development_path(self, gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate ordered development path based on gaps.
        
        Orders gaps by severity and dependencies.
        """
        # Sort by severity (critical → high → medium)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_gaps = sorted(gaps, key=lambda x: severity_order.get(x["severity"], 99))

        path = []
        for idx, gap in enumerate(sorted_gaps, 1):
            path.append({
                "step": idx,
                "skill": gap["skill"],
                "current": gap["current"],
                "target": gap["required"],
                "severity": gap["severity"],
                "estimated_hours": self._estimate_learning_hours(gap["required"] - gap["current"]),
            })

        return path

    def _estimate_learning_hours(self, level_gap: float) -> int:
        """Estimate learning hours needed to close skill gap."""
        # Rough estimation: 40 hours per skill level
        return int(level_gap * 40)

    def simulate_improvement(self, current_compatibility: float, improvements: dict[str, float]) -> dict[str, Any]:
        """Simulate improvement in compatibility with given actions.
        
        Args:
            current_compatibility: Current compatibility percentage
            improvements: Dictionary with improvement percentages
            
        Returns:
            Simulated compatibility and impact
        """
        improvement_impact = sum(improvements.values())
        new_compatibility = min(100, current_compatibility + improvement_impact)
        increase = new_compatibility - current_compatibility

        return {
            "current": round(current_compatibility, 1),
            "simulated": round(new_compatibility, 1),
            "increase": round(increase, 1),
            "improvements": improvements,
        }
