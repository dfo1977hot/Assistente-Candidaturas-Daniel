"""Insight generator for creating actionable insights from patterns."""

from typing import Any
from datetime import datetime

from acd.domain.learning.insight import Insight, InsightType
from acd.domain.learning.pattern import Pattern, PatternType
from acd.domain.learning.hypothesis import Hypothesis


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
        """Generate insight from pattern data.

        Args:
            pattern_data: Pattern dictionary
            related_patterns: IDs of related patterns
            related_hypotheses: IDs of related hypotheses

        Returns:
            Insight data
        """
        pattern_type = pattern_data.get("type", "")

        # Generate recommendations based on pattern type
        recommendations = self._generate_recommendations(pattern_data)

        # Generate title and description
        title, description = self._generate_title_and_description(pattern_data)

        # Calculate impact
        impact_score = pattern_data.get("impact", 0.0)
        expected_impact = self._describe_impact(impact_score, pattern_type)

        insight = {
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
            "analysis_period_end": datetime.utcnow(),
        }

        return insight

    def _generate_title_and_description(self, pattern_data: dict[str, Any]) -> tuple[str, str]:
        """Generate title and description from pattern.

        Args:
            pattern_data: Pattern dictionary

        Returns:
            Tuple of (title, description)
        """
        name = pattern_data.get("name", "")
        criteria = pattern_data.get("criteria", {})
        evidence = pattern_data.get("evidence_count", 0)
        confidence = pattern_data.get("confidence", 0.5)

        title = f"{name}"
        description = f"{pattern_data.get('description', '')} Based on {evidence} applications with {confidence*100:.0f}% confidence."

        return title, description

    def _generate_recommendations(self, pattern_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate recommendations based on pattern.

        Args:
            pattern_data: Pattern dictionary

        Returns:
            List of recommendations
        """
        pattern_type = pattern_data.get("type", "")
        criteria = pattern_data.get("criteria", {})
        impact = pattern_data.get("impact", 0.0)

        recommendations = []

        if pattern_type == PatternType.SKILL_SUCCESS.value:
            recommendations.append({
                "action": f"Emphasize {criteria.get('skill')} skill in applications",
                "rationale": f"This skill appears in {criteria.get('applications')} successful applications",
                "expected_benefit": f"Could improve success rate by ~{impact*100:.0f}%",
            })

        elif pattern_type == PatternType.PLATFORM_SUCCESS.value:
            recommendations.append({
                "action": f"Prioritize applications on {criteria.get('platform')}",
                "rationale": f"{criteria.get('platform')} has shown high conversion ({criteria.get('min_conversion')*100:.0f}%)",
                "expected_benefit": f"Could improve success rate by ~{impact*100:.0f}%",
            })

        elif pattern_type == PatternType.SECTOR_PATTERN.value:
            recommendations.append({
                "action": f"Target {criteria.get('sector')} sector positions",
                "rationale": f"Your profile aligns well with {criteria.get('sector')} sector",
                "expected_benefit": f"Could improve success rate by ~{impact*100:.0f}%",
            })

        elif pattern_type == PatternType.TIMING_PATTERN.value:
            day_name = criteria.get("day_name", "Monday")
            recommendations.append({
                "action": f"Submit applications on {day_name}",
                "rationale": f"Applications submitted on {day_name} have {criteria.get('success_rate')*100:.0f}% success rate",
                "expected_benefit": f"Could improve response time and success rate",
            })

        elif pattern_type == PatternType.RESUME_TYPE_SUCCESS.value:
            recommendations.append({
                "action": f"Use resume version {criteria.get('resume_id')} for similar positions",
                "rationale": f"This resume version achieved {criteria.get('success_rate')*100:.0f}% success rate",
                "expected_benefit": f"Could improve interview rate by ~{impact*100:.0f}%",
            })

        return recommendations if recommendations else [{
            "action": "Review the pattern details above",
            "rationale": pattern_data.get("description", ""),
            "expected_benefit": f"~{impact*100:.0f}% improvement potential",
        }]

    def _map_pattern_to_insight_type(self, pattern_type: str) -> str:
        """Map pattern type to insight type.

        Args:
            pattern_type: Pattern type string

        Returns:
            Insight type string
        """
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
        return mapping.get(pattern_type, InsightType.GENERAL_RECOMMENDATION.value)

    def _describe_impact(self, impact: float, pattern_type: str) -> str:
        """Describe expected impact in human language.

        Args:
            impact: Impact score (0-1)
            pattern_type: Pattern type

        Returns:
            Impact description
        """
        impact_pct = impact * 100

        if impact_pct >= 30:
            magnitude = "significant"
        elif impact_pct >= 15:
            magnitude = "moderate"
        elif impact_pct >= 5:
            magnitude = "small but measurable"
        else:
            magnitude = "minimal"

        return f"Applying this insight could have a {magnitude} impact (estimated +{impact_pct:.0f}%) on your success rate."

    def generate_multiple(
        self,
        patterns: list[dict[str, Any]],
        max_insights: int = 10,
    ) -> list[dict[str, Any]]:
        """Generate multiple insights from patterns.

        Args:
            patterns: List of pattern dictionaries
            max_insights: Maximum insights to generate

        Returns:
            List of insights
        """
        insights = []

        for pattern in patterns[:max_insights]:
            insight = self.generate_from_pattern(pattern)
            insights.append(insight)

        return insights
