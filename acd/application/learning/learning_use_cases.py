"""Application layer use cases for learning functionality."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from acd.services.learning import ApprovalService, KnowledgeReuseService, LearningService


@dataclass
class RegisterOutcomeRequest:
    """Request for registering an outcome."""

    outcome_type: str
    result: str
    company: str
    position_title: str
    skills: list[str] | None = None
    platform: str | None = None
    sector: str | None = None
    curriculum_id: int | None = None
    context: dict[str, Any] | None = None


@dataclass
class ApproveRecordRequest:
    """Request for approving a record."""

    record_id: int
    notes: str = ""


@dataclass
class RejectRecordRequest:
    """Request for rejecting a record."""

    record_id: int
    notes: str = ""


class LearningUseCases:
    """Use cases for learning functionality."""

    def __init__(self, session: Session) -> None:
        """Initialize use cases.

        Args:
            session: SQLAlchemy session
        """
        self.learning_service = LearningService(session)
        self.approval_service = ApprovalService(session)
        self.knowledge_service = KnowledgeReuseService(session)

    def register_outcome(self, request: RegisterOutcomeRequest) -> dict[str, Any]:
        """Register an application outcome.

        Args:
            request: Registration request

        Returns:
            Registration result
        """
        return self.learning_service.register_outcome(
            outcome_type=request.outcome_type,
            result=request.result,
            company=request.company,
            position_title=request.position_title,
            skills=request.skills,
            platform=request.platform,
            sector=request.sector,
            curriculum_id=request.curriculum_id,
        )

    def evaluate_patterns(
        self,
        days_back: int = 90,
        pattern_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Evaluate patterns from historical data.

        Args:
            days_back: Days of data to analyze
            pattern_types: Specific pattern types to detect

        Returns:
            Pattern evaluation result
        """
        return self.learning_service.detect_patterns(
            days_back=days_back,
            pattern_types=pattern_types,
        )

    def generate_insights(self, limit: int = 10) -> dict[str, Any]:
        """Generate insights from patterns.

        Args:
            limit: Maximum insights to generate

        Returns:
            Insights generation result
        """
        return self.learning_service.generate_insights(limit=limit)

    def get_pending_approvals(self, limit: int = 50) -> dict[str, Any]:
        """Get learning items pending approval.

        Args:
            limit: Maximum items to return

        Returns:
            Pending items
        """
        pending = self.approval_service.get_pending_approvals(limit=limit)
        return {
            "success": True,
            "pending_items": pending,
            "total": len(pending),
        }

    def approve_record(self, request: ApproveRecordRequest) -> dict[str, Any]:
        """Approve a learning record.

        Args:
            request: Approval request

        Returns:
            Approval result
        """
        return self.approval_service.approve_learning_record(
            record_id=request.record_id,
            approver_notes=request.notes,
        )

    def reject_record(self, request: RejectRecordRequest) -> dict[str, Any]:
        """Reject a learning record.

        Args:
            request: Rejection request

        Returns:
            Rejection result
        """
        return self.approval_service.reject_learning_record(
            record_id=request.record_id,
            rejection_notes=request.notes,
        )

    def get_applicable_recommendations(self, limit: int = 10) -> dict[str, Any]:
        """Get applicable recommendations.

        Args:
            limit: Maximum recommendations to return

        Returns:
            Recommendations
        """
        insights = self.knowledge_service.get_applicable_insights(limit=limit)
        return {
            "success": True,
            "recommendations": insights,
            "total": len(insights),
        }

    def get_skill_recommendations(
        self,
        current_skills: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get skill recommendations.

        Args:
            current_skills: Current user skills

        Returns:
            Skill recommendations
        """
        recommendations = self.knowledge_service.get_skill_recommendations(
            current_skills=current_skills
        )
        return {
            "success": True,
            "recommendations": recommendations,
            "total": len(recommendations),
        }

    def get_platform_recommendations(self) -> dict[str, Any]:
        """Get platform recommendations.

        Returns:
            Platform recommendations
        """
        recommendations = self.knowledge_service.get_platform_recommendations()
        return {
            "success": True,
            "recommendations": recommendations,
            "total": len(recommendations),
        }

    def get_timing_advice(self) -> dict[str, Any]:
        """Get timing advice for submissions.

        Returns:
            Timing recommendations
        """
        advice = self.knowledge_service.get_timing_recommendations()
        return {
            "success": True,
            "advice": advice,
        }

    def apply_insight(self, insight_id: int) -> dict[str, Any]:
        """Apply an insight.

        Args:
            insight_id: Insight ID

        Returns:
            Application result
        """
        return self.knowledge_service.apply_insight(insight_id)

    def get_statistics(self) -> dict[str, Any]:
        """Get learning statistics.

        Returns:
            Statistics
        """
        stats = self.learning_service.get_statistics()
        return {
            "success": True,
            "statistics": stats,
        }

    def get_learning_health(self) -> dict[str, Any]:
        """Get overall learning system health.

        Returns:
            Health report
        """
        health = self.learning_service.get_learning_health()
        return {
            "success": True,
            "health": health,
        }

    def get_impact_metrics(self) -> dict[str, Any]:
        """Get impact of applied knowledge.

        Returns:
            Impact metrics
        """
        impact = self.knowledge_service.get_knowledge_impact()
        return {
            "success": True,
            "impact": impact,
        }
