"""Knowledge reuse service for applying learned patterns."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from sqlalchemy.orm import Session

from acd.infrastructure.repositories.learning import LearningRepository

logger = logging.getLogger(__name__)


class KnowledgeReuseService:
    """Service for reusing learned knowledge."""

    def __init__(self, session: Session) -> None:
        """Initialize knowledge reuse service.

        Args:
            session: SQLAlchemy session.
        """
        self.repository = LearningRepository(session)

    def get_applicable_insights(
        self,
        context: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get insights applicable to current context."""
        insights = self.repository.list_insights(
            is_actionable=True,
            limit=limit * 2,
        )

        result: list[dict[str, Any]] = []

        for insight in insights:
            if context:
                if self._insight_matches_context(insight, context):
                    result.append(self._format_insight(insight))
            else:
                result.append(self._format_insight(insight))

            if len(result) >= limit:
                break

        return result

    def get_skill_recommendations(
        self,
        current_skills: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get skill recommendations based on learned patterns."""

        del current_skills

        insights = self.repository.list_insights(
            is_actionable=True,
            limit=100,
        )

        recommendations: list[dict[str, Any]] = []

        for insight in insights:
            if insight.insight_type == "SKILL_RECOMMENDATION":
                for rec in insight.recommendations:
                    recommendations.append(
                        {
                            "skill": rec.get(
                                "action",
                                "",
                            )
                            .replace("Emphasize ", "")
                            .split(" ")[0],
                            "rationale": rec.get(
                                "rationale",
                                "",
                            ),
                            "expected_benefit": rec.get(
                                "expected_benefit",
                                "",
                            ),
                            "confidence": insight.confidence,
                            "source": insight.title,
                        }
                    )

        return recommendations[:10]

    def get_platform_recommendations(
        self,
    ) -> list[dict[str, Any]]:
        """Get platform recommendations based on learned patterns."""

        insights = self.repository.list_insights(
            is_actionable=True,
            limit=100,
        )

        recommendations: list[dict[str, Any]] = []

        for insight in insights:
            if insight.insight_type == "PLATFORM_ADVICE":
                for rec in insight.recommendations:
                    recommendations.append(
                        {
                            "platform": rec.get("action", ""),
                            "rationale": rec.get("rationale", ""),
                            "success_rate": rec.get(
                                "expected_benefit",
                                "",
                            ),
                            "confidence": insight.confidence,
                        }
                    )

        return recommendations

    def get_timing_recommendations(
        self,
    ) -> dict[str, Any]:
        """Get timing recommendations."""

        insights = self.repository.list_insights(
            is_actionable=True,
            limit=100,
        )

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
                            "recommendation": rec.get(
                                "action",
                                "",
                            ),
                            "rationale": rec.get(
                                "rationale",
                                "",
                            ),
                            "confidence": insight.confidence,
                        }
                    )

        return timing_info

    def get_letter_improvements(
        self,
    ) -> list[dict[str, Any]]:
        """Get recommendations for improving letters."""

        insights = self.repository.list_insights(
            is_actionable=True,
            limit=100,
        )

        improvements: list[dict[str, Any]] = []

        for insight in insights:
            if insight.insight_type == "LETTER_IMPROVEMENT":
                for rec in insight.recommendations:
                    improvements.append(
                        {
                            "improvement": rec.get("action", ""),
                            "rationale": rec.get("rationale", ""),
                            "expected_impact": rec.get(
                                "expected_benefit",
                                "",
                            ),
                            "confidence": insight.confidence,
                        }
                    )

        return improvements

    def get_sector_strategy(
        self,
        sector: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get sector-specific strategy."""

        insights = self.repository.list_insights(
            is_actionable=True,
            limit=100,
        )

        strategies: list[dict[str, Any]] = []

        for insight in insights:
            if insight.insight_type == "SECTOR_STRATEGY":
                if sector is None or sector.lower() in insight.description.lower():
                    for rec in insight.recommendations:
                        strategies.append(
                            {
                                "strategy": rec.get("action", ""),
                                "sector": sector or "General",
                                "rationale": rec.get(
                                    "rationale",
                                    "",
                                ),
                                "expected_benefit": rec.get(
                                    "expected_benefit",
                                    "",
                                ),
                                "confidence": insight.confidence,
                            }
                        )

        return strategies

    def apply_insight(
        self,
        insight_id: int,
    ) -> dict[str, Any]:
        """Mark insight as applied."""

        success = self.repository.mark_insight_applied(
            insight_id,
        )

        return {
            "success": success,
            "insight_id": insight_id,
            "applied_at": (
                datetime.now(UTC).isoformat()
                if success
                else None
            ),
        }

    def get_knowledge_impact(
        self,
    ) -> dict[str, Any]:
        """Get impact of applied knowledge."""

        insights = self.repository.list_insights(
            is_applied=True,
            limit=1000,
        )

        impact = {
            "total_applied_insights": len(insights),
            "average_confidence": 0.0,
            "estimated_improvement": 0.0,
        }

        if insights:
            confidence_sum = sum(
                insight.confidence
                for insight in insights
            )

            impact["average_confidence"] = (
                confidence_sum / len(insights)
            )

            improvements: list[float] = []

            for insight in insights:
                if "Could improve" in insight.expected_impact:
                    try:
                        percentage = float(
                            insight.expected_impact.split("+")[1]
                            .split("%")[0]
                        )
                        improvements.append(
                            percentage,
                        )
                    except (
                        IndexError,
                        ValueError,
                    ):
                        logger.debug(
                            "Unable to parse expected impact: %s",
                            insight.expected_impact,
                        )

            if improvements:
                impact["estimated_improvement"] = (
                    sum(improvements)
                    / len(improvements)
                )

        return impact

    def _insight_matches_context(
        self,
        insight: Any,
        context: dict[str, Any],
    ) -> bool:
        """Check whether an insight matches the current context."""

        for recommendation in insight.recommendations:
            action = str(
                recommendation.get(
                    "action",
                    "",
                )
            ).lower()

            for value in context.values():
                if (
                    isinstance(value, str)
                    and value.lower() in action
                ):
                    return True

                if isinstance(value, list):
                    if any(
                        str(item).lower() in action
                        for item in value
                    ):
                        return True

        return True

    def _format_insight(
        self,
        insight: Any,
    ) -> dict[str, Any]:
        """Format insight for presentation."""

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