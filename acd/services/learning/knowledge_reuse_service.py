"""Knowledge reuse service for applying learned patterns."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from acd.infrastructure.repositories.learning import LearningRepository


class KnowledgeReuseService:
    """Service for reusing learned knowledge."""

    def __init__(self, session: Session) -> None:
        """Initialize knowledge reuse service.

        Args:
            session: SQLAlchemy session
        """
        self.repository = LearningRepository(session)

    def get_applicable_insights(
        self,
        context: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get insights applicable to current context.

        Args:
            context: Current context (skills, platform, sector, etc)
            limit: Maximum insights to return

        Returns:
            List of applicable insights
        """
        insights = self.repository.list_insights(is_actionable=True, limit=limit * 2)

        result = []
        for insight in insights:
            # Check if insight matches context
            if context:
                matches = self._insight_matches_context(insight, context)
                if matches:
                    result.append(self._format_insight(insight))
            else:
                result.append(self._format_insight(insight))

            if len(result) >= limit:
                break

        return result

    def get_skill_recommendations(
        self, current_skills: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get skill recommendations based on learned patterns.

        Args:
            current_skills: Current user skills

        Returns:
            Skill recommendations
        """
        insights = self.repository.list_insights(is_actionable=True, limit=100)

        recommendations = []
        for insight in insights:
            if insight.insight_type == "SKILL_RECOMMENDATION":
                for rec in insight.recommendations:
                    recommendations.append(
                        {
                            "skill": rec.get("action", "").replace("Emphasize ", "").split(" ")[0],
                            "rationale": rec.get("rationale", ""),
                            "expected_benefit": rec.get("expected_benefit", ""),
                            "confidence": insight.confidence,
                            "source": insight.title,
                        }
                    )

        return recommendations[:10]

    def get_platform_recommendations(self) -> list[dict[str, Any]]:
        """Get platform recommendations based on learned patterns.

        Returns:
            Platform recommendations
        """
        insights = self.repository.list_insights(is_actionable=True, limit=100)

        recommendations = []
        for insight in insights:
            if insight.insight_type == "PLATFORM_ADVICE":
                for rec in insight.recommendations:
                    recommendations.append(
                        {
                            "platform": rec.get("action", ""),
                            "rationale": rec.get("rationale", ""),
                            "success_rate": rec.get("expected_benefit", ""),
                            "confidence": insight.confidence,
                        }
                    )

        return recommendations

    def get_timing_recommendations(self) -> dict[str, Any]:
        """Get timing recommendations for submissions.

        Returns:
            Timing information
        """
        insights = self.repository.list_insights(is_actionable=True, limit=100)

        timing_info = {
            "best_day": None,
            "best_time": None,
            "recommendations": [],
        }

        for insight in insights:
            if insight.insight_type == "TIMING_INSIGHT":
                for rec in insight.recommendations:
                    timing_info["recommendations"].append(
                        {
                            "recommendation": rec.get("action", ""),
                            "rationale": rec.get("rationale", ""),
                            "confidence": insight.confidence,
                        }
                    )

        return timing_info

    def get_letter_improvements(self) -> list[dict[str, Any]]:
        """Get recommendations for improving letters.

        Returns:
            Letter improvement suggestions
        """
        insights = self.repository.list_insights(is_actionable=True, limit=100)

        improvements = []
        for insight in insights:
            if insight.insight_type == "LETTER_IMPROVEMENT":
                for rec in insight.recommendations:
                    improvements.append(
                        {
                            "improvement": rec.get("action", ""),
                            "rationale": rec.get("rationale", ""),
                            "expected_impact": rec.get("expected_benefit", ""),
                            "confidence": insight.confidence,
                        }
                    )

        return improvements

    def get_sector_strategy(self, sector: str | None = None) -> list[dict[str, Any]]:
        """Get sector-specific strategy.

        Args:
            sector: Specific sector or None for all

        Returns:
            Sector strategies
        """
        insights = self.repository.list_insights(is_actionable=True, limit=100)

        strategies = []
        for insight in insights:
            if insight.insight_type == "SECTOR_STRATEGY":
                if sector is None or sector.lower() in insight.description.lower():
                    for rec in insight.recommendations:
                        strategies.append(
                            {
                                "strategy": rec.get("action", ""),
                                "sector": sector or "General",
                                "rationale": rec.get("rationale", ""),
                                "expected_benefit": rec.get("expected_benefit", ""),
                                "confidence": insight.confidence,
                            }
                        )

        return strategies

    def apply_insight(self, insight_id: int) -> dict[str, Any]:
        """Mark insight as applied.

        Args:
            insight_id: Insight ID

        Returns:
            Application result
        """
        success = self.repository.mark_insight_applied(insight_id)

        return {
            "success": success,
            "insight_id": insight_id,
            "applied_at": datetime.now(UTC).isoformat() if success else None,
        }

    def get_knowledge_impact(self) -> dict[str, Any]:
        """Get impact of applied knowledge.

        Returns:
            Impact metrics
        """
        insights = self.repository.list_insights(is_applied=True, limit=1000)

        impact = {
            "total_applied_insights": len(insights),
            "average_confidence": 0.0,
            "estimated_improvement": 0.0,
        }

        if insights:
            confidence_sum = sum(i.confidence for i in insights)
            impact["average_confidence"] = confidence_sum / len(insights)

            # Estimate improvement from expected_impact fields
            improvements = []
            for insight in insights:
                if "Could improve" in insight.expected_impact:
                    try:
                        pct = float(insight.expected_impact.split("+")[1].split("%")[0])
                        improvements.append(pct)
                    except IndexError, ValueError:
                        pass

            if improvements:
                impact["estimated_improvement"] = sum(improvements) / len(improvements)

        return impact

    def _insight_matches_context(self, insight: Any, context: dict[str, Any]) -> bool:
        """Check if insight matches current context.

        Args:
            insight: Insight to check
            context: Current context

        Returns:
            True if matches
        """
        # Check if insight recommendations mention context items
        for rec in insight.recommendations:
            action = str(rec.get("action", "")).lower()
            for _key, value in context.items():
                if isinstance(value, str) and value.lower() in action:
                    return True
                elif isinstance(value, list):
                    for v in value:
                        if str(v).lower() in action:
                            return True
        return True  # Default to including if no specific match

    def _format_insight(self, insight: Any) -> dict[str, Any]:
        """Format insight for presentation.

        Args:
            insight: Insight to format

        Returns:
            Formatted insight
        """
        return {
            "id": insight.id,
            "title": insight.title,
            "description": insight.description,
            "type": insight.insight_type,
            "confidence": insight.confidence,
            "expected_impact": insight.expected_impact,
            "recommendations": insight.recommendations,
            "is_applied": insight.is_applied,
        }
