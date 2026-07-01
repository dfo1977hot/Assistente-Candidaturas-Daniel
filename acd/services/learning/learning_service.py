"""Learning service for orchestrating learning operations."""

from typing import Any
from datetime import datetime

from sqlalchemy.orm import Session

from acd.domain.learning.outcome import Outcome
from acd.infrastructure.learning import LearningEngine
from acd.infrastructure.repositories.learning import LearningRepository


class LearningService:
    """Service for learning operations."""

    def __init__(self, session: Session) -> None:
        """Initialize learning service.

        Args:
            session: SQLAlchemy session
        """
        self.repository = LearningRepository(session)
        self.engine = LearningEngine()
        self.session = session

    def register_outcome(
        self,
        outcome_type: str,
        result: str,
        company: str,
        position_title: str,
        skills: list[str] | None = None,
        platform: str | None = None,
        sector: str | None = None,
        curriculum_id: int | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """Register application outcome and trigger learning.

        Args:
            outcome_type: Type of outcome
            result: Result (success/failure/etc)
            company: Company name
            position_title: Position title
            skills: List of skills mentioned
            platform: Platform name
            sector: Sector
            curriculum_id: Curriculum ID
            **kwargs: Additional fields

        Returns:
            Registration result
        """
        # Create outcome
        outcome = self.repository.create_outcome(
            outcome_type=outcome_type,
            result=result,
            company=company,
            position_title=position_title,
            skills_mentioned=skills or [],
            platform=platform,
            sector=sector,
            curriculum_id=curriculum_id,
            **kwargs
        )

        # Process outcome through learning engine
        result = self.engine.process_outcome(outcome, auto_detect_patterns=False)
        result["outcome_id"] = outcome.id

        return result

    def detect_patterns(
        self,
        days_back: int = 90,
        pattern_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Detect patterns from outcomes.

        Args:
            days_back: Days of data to analyze
            pattern_types: Specific pattern types to detect

        Returns:
            Pattern detection result
        """
        # Get outcomes from repository
        outcomes = self.repository.list_outcomes(days_back=days_back, limit=1000)

        if not outcomes:
            return {
                "success": True,
                "patterns_detected": 0,
                "patterns": [],
            }

        # Detect patterns
        patterns = self.engine.detect_patterns(outcomes, pattern_types)

        # Save patterns to repository
        saved_patterns = []
        for pattern_result in patterns:
            pattern_data = pattern_result["pattern"]
            saved_pattern = self.repository.create_pattern(
                name=pattern_data.get("name", ""),
                description=pattern_data.get("description", ""),
                pattern_type=pattern_data.get("type", ""),
                criteria=pattern_data.get("criteria", {}),
                evidence_count=pattern_data.get("evidence_count", 0),
                confidence=pattern_data.get("confidence", 0.5),
            )
            saved_patterns.append({
                "id": saved_pattern.id,
                "pattern": pattern_data,
                "requires_approval": pattern_result["requires_approval"],
            })

        return {
            "success": True,
            "patterns_detected": len(saved_patterns),
            "patterns": saved_patterns,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def generate_insights(
        self,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Generate insights from detected patterns.

        Args:
            limit: Maximum insights to generate

        Returns:
            Insight generation result
        """
        # Get active patterns
        patterns_data = []
        patterns = self.repository.list_patterns(is_active=True, limit=limit)

        for pattern in patterns:
            patterns_data.append({
                "name": pattern.name,
                "description": pattern.description,
                "type": pattern.pattern_type,
                "criteria": pattern.criteria,
                "evidence_count": pattern.evidence_count,
                "confidence": pattern.confidence,
                "impact": 0.3,  # Can be calculated from criteria
            })

        # Generate insights
        insights_results = self.engine.generate_insights(patterns_data, max_insights=limit)

        # Save insights to repository
        saved_insights = []
        for insight_result in insights_results:
            insight_data = insight_result["insight"]
            saved_insight = self.repository.create_insight(
                title=insight_data.get("title", ""),
                description=insight_data.get("description", ""),
                insight_type=insight_data.get("insight_type", ""),
                expected_impact=insight_data.get("expected_impact", ""),
                confidence=insight_data.get("confidence", 0.5),
                recommendations=insight_data.get("recommendations", []),
            )
            saved_insights.append({
                "id": saved_insight.id,
                "insight": insight_data,
                "requires_approval": insight_result["requires_approval"],
            })

        return {
            "success": True,
            "insights_generated": len(saved_insights),
            "insights": saved_insights,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_pending_approvals(self) -> dict[str, list]:
        """Get all learning items pending approval.

        Returns:
            Pending items organized by type
        """
        pending_records = self.repository.list_records(status="DETECTED", limit=100)
        pending_hypotheses = self.repository.list_hypotheses(status="PROPOSED", limit=50)

        return {
            "learning_records": pending_records,
            "hypotheses": pending_hypotheses,
            "total_pending": len(pending_records) + len(pending_hypotheses),
        }

    def approve_learning(self, record_id: int, notes: str = "") -> bool:
        """Approve learning record.

        Args:
            record_id: Record ID
            notes: Approval notes

        Returns:
            True if successful
        """
        return self.repository.approve_record(record_id, notes)

    def reject_learning(self, record_id: int, notes: str = "") -> bool:
        """Reject learning record.

        Args:
            record_id: Record ID
            notes: Rejection notes

        Returns:
            True if successful
        """
        return self.repository.reject_record(record_id, notes)

    def get_recommendations(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get current recommendations from applied insights.

        Args:
            limit: Maximum recommendations to return

        Returns:
            List of recommendations
        """
        insights = self.repository.list_insights(is_actionable=True, is_applied=False, limit=limit)

        recommendations = []
        for insight in insights:
            recommendations.extend(insight.recommendations)

        return recommendations[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """Get learning statistics.

        Returns:
            Statistics dictionary
        """
        stats = self.repository.get_statistics()
        engine_stats = self.engine.get_statistics()

        return {
            **stats,
            **engine_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_learning_health(self) -> dict[str, Any]:
        """Get overall learning health.

        Returns:
            Health report
        """
        return self.engine.get_health_report()
