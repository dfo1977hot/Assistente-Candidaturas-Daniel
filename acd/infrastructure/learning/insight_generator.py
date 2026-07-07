from __future__ import annotations

"""Insight generator for creating actionable insights from patterns."""

from datetime import UTC, datetime
from typing import Any

from acd.domain.learning.insight import InsightType
from acd.domain.learning.pattern import PatternType


class InsightGenerator:
    """Generates actionable insights from patterns and hypotheses."""

    def __init__(self) -> None:
        """Initialize insight generator."""
        pass

    def generate_from_pattern(
        self,
        pattern_data: dict[str, Any],
        related_patterns: list[int] | None = None,
        related_hypotheses: list[int] | None = None,
    ) -> dict[str, Any]:
        """Generate insight from pattern data."""

        pattern_type = pattern_data.get("type", "")

        recommendations = self._generate_recommendations(pattern_data)

        title, description = self._generate_title_and_description(pattern_data)

        impact_score = pattern_data.get("impact", 0.0)
        expected_impact = self._describe_impact(impact_score, pattern_type)

        return {
            "title": title,
            "description": description,
            "insight_type": self._map_pattern_to_insight_type(pattern_type),
            "expected_impact": expected_impact,
            "confidence": pattern_data.get("confidence", 0.5),
            "origin": f"Pattern: {pattern_data.get('name')}",
            "related_patterns": related_patterns or [pattern_data.get("name")],
            "related_hypotheses": related_hypotheses or [],
            "recommendations": recommendations,
            "evidence_summary": {
                "evidence_count": pattern_data.get("evidence_count", 0),
                "criteria": pattern_data.get("criteria", {}),
                "impact_score": impact_score,
            },
            "data_points_analyzed": pattern_data.get("evidence_count", 0),
            "is_actionable": True,
            "analysis_period_start": None,
            "analysis_period_end": datetime.now(UTC),
        }

    def _generate_title_and_description(
        self,
        pattern_data: dict[str, Any],
    ) -> tuple[str, str]:
        """Generate title and description from pattern."""

        name = pattern_data.get("name", "")
        criteria = pattern_data.get("criteria", {})
        evidence = pattern_data.get("evidence_count", 0)
        confidence = pattern_data.get("confidence", 0.5)

        title = name

        description = (
            f"{pattern_data.get('description', '')} "
            f"Based on {evidence} applications "
            f"with {confidence * 100:.0f}% confidence."
        )

        # evita variável não utilizada (útil para futuras melhorias)
        _ = criteria

        return title, description

    def _generate_recommendations(
        self,
        pattern_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate recommendations based on pattern."""

        pattern_type = pattern_data.get("type", "")
        criteria = pattern_data.get("criteria", {})
        impact = pattern_data.get("impact", 0.0)

        recommendations: list[dict[str, Any]] = []

        if pattern_type == PatternType.SKILL_SUCCESS.value:

            recommendations.append(
                {
                    "action": (
                        f"Emphasize {criteria.get('skill', 'this')} skill "
                        "in applications"
                    ),
                    "rationale": (
                        "This skill appears in "
                        f"{criteria.get('applications', 0)} "
                        "successful applications"
                    ),
                    "expected_benefit": (
                        f"Could improve success rate by ~{impact * 100:.0f}%"
                    ),
                }
            )

        elif pattern_type == PatternType.PLATFORM_SUCCESS.value:

            platform = criteria.get("platform", "this platform")

            recommendations.append(
                {
                    "action": f"Prioritize applications on {platform}",
                    "rationale": (
                        f"{platform} has shown high conversion "
                        f"({criteria.get('min_conversion', 0) * 100:.0f}%)"
                    ),
                    "expected_benefit": (
                        f"Could improve success rate by ~{impact * 100:.0f}%"
                    ),
                }
            )

        elif pattern_type == PatternType.SECTOR_PATTERN.value:

            sector = criteria.get("sector", "this sector")

            recommendations.append(
                {
                    "action": f"Target {sector} sector positions",
                    "rationale": f"Your profile aligns well with {sector} sector",
                    "expected_benefit": (
                        f"Could improve success rate by ~{impact * 100:.0f}%"
                    ),
                }
            )

        elif pattern_type == PatternType.TIMING_PATTERN.value:

            day_name = criteria.get("day_name", "Monday")

            recommendations.append(
                {
                    "action": f"Submit applications on {day_name}",
                    "rationale": (
                        f"Applications submitted on {day_name} "
                        f"have {criteria.get('success_rate', 0) * 100:.0f}% "
                        "success rate"
                    ),
                    "expected_benefit": (
                        "Could improve response time and success rate"
                    ),
                }
            )

        elif pattern_type == PatternType.RESUME_TYPE_SUCCESS.value:

            recommendations.append(
                {
                    "action": (
                        f"Use resume version "
                        f"{criteria.get('resume_id', 'recommended')} "
                        "for similar positions"
                    ),
                    "rationale": (
                        "This resume version achieved "
                        f"{criteria.get('success_rate', 0) * 100:.0f}% "
                        "success rate"
                    ),
                    "expected_benefit": (
                        f"Could improve interview rate by ~{impact * 100:.0f}%"
                    ),
                }
            )

        if recommendations:
            return recommendations

        return [
            {
                "action": "Review the pattern details above",
                "rationale": pattern_data.get("description", ""),
                "expected_benefit": (
                    f"~{impact * 100:.0f}% improvement potential"
                ),
            }
        ]

    def _map_pattern_to_insight_type(self, pattern_type: str) -> str:
        """Map pattern type to insight type."""

        mapping = {
            PatternType.SKILL_SUCCESS.value: InsightType.SKILL_RECOMMENDATION.value,
            PatternType.PLATFORM_SUCCESS.value: InsightType.PLATFORM_ADVICE.value,
            PatternType.SECTOR_PATTERN.value: InsightType.SECTOR_STRATEGY.value,
            PatternType.TIMING_PATTERN.value: InsightType.TIMING_INSIGHT.value,
            PatternType.RESUME_TYPE_SUCCESS.value: InsightType.RESUME_OPTIMIZATION.value,
            PatternType.CONVERSION_RATE.value: InsightType.CONVERSION_TIP.value,
            PatternType.RESPONSE_TIME.value: InsightType.TIMING_INSIGHT.value,
            PatternType.LETTER_EFFECTIVENESS.value: InsightType.LETTER_IMPROVEMENT.value,
        }

        return mapping.get(
            pattern_type,
            InsightType.GENERAL_RECOMMENDATION.value,
        )

    def _describe_impact(
        self,
        impact: float,
        pattern_type: str,
    ) -> str:
        """Describe expected impact."""

        del pattern_type

        impact_pct = impact * 100

        if impact_pct >= 30:
            magnitude = "significant"
        elif impact_pct >= 15:
            magnitude = "moderate"
        elif impact_pct >= 5:
            magnitude = "small but measurable"
        else:
            magnitude = "minimal"

        return (
            f"Applying this insight could have a {magnitude} impact "
            f"(estimated +{impact_pct:.0f}%) on your success rate."
        )

    def generate_multiple(
        self,
        patterns: list[dict[str, Any]],
        max_insights: int = 10,
    ) -> list[dict[str, Any]]:
        """Generate multiple insights."""

        return [
            self.generate_from_pattern(pattern)
            for pattern in patterns[:max_insights]
        ]