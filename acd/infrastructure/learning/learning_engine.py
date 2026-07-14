"""Central learning engine for coordinating learning activities."""

from datetime import UTC, datetime
from typing import Any

from acd.domain.learning.learning_record import LearningRecord
from acd.domain.learning.outcome import Outcome
from acd.infrastructure.learning.confidence_calculator import (
    ConfidenceCalculator,
)
from acd.infrastructure.learning.evidence_aggregator import (
    EvidenceAggregator,
)
from acd.infrastructure.learning.insight_generator import (
    InsightGenerator,
)
from acd.infrastructure.learning.learning_policy_engine import (
    LearningEventType,
    LearningPolicyEngine,
)
from acd.infrastructure.learning.pattern_detector import PatternDetector


class LearningEngine:
    """Central orchestrator for learning and pattern detection."""

    def __init__(self) -> None:
        """Initialize learning engine."""
        self.pattern_detector = PatternDetector()
        self.insight_generator = InsightGenerator()
        self.evidence_aggregator = EvidenceAggregator()
        self.confidence_calculator = ConfidenceCalculator()
        self.policy_engine = LearningPolicyEngine()

        self.stats: dict[str, int] = self._create_statistics()

    def _create_statistics(self) -> dict[str, int]:
        """Create an empty statistics dictionary."""

        return {
            "patterns_detected": 0,
            "insights_generated": 0,
            "hypotheses_proposed": 0,
            "learning_records_approved": 0,
            "learning_records_rejected": 0,
        }

    def process_outcome(
        self,
        outcome: Outcome,
        auto_detect_patterns: bool = True,
    ) -> dict[str, Any]:
        """Process an outcome and optionally detect patterns.

        Args:
            outcome: Outcome to process.
            auto_detect_patterns: Whether to auto-detect patterns.

        Returns:
            Processing result.
        """
        result = {
            "outcome_id": outcome.id,
            "outcome_recorded": True,
            "patterns_detected": [],
            "insights_generated": [],
            "hypotheses_proposed": [],
        }

        if not self.policy_engine.should_process_event(
            LearningEventType.OUTCOME_RECORDED.value,
        ):
            return result

        # Learning record persistence is handled by the repository layer
        # when repository integration is enabled.

        if auto_detect_patterns:
            result["patterns_detected"].append(
                {
                    "type": "outcome_recorded",
                    "outcome_id": outcome.id,
                }
            )

        return result

    def detect_patterns(
        self,
        outcomes: list[Outcome],
        pattern_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Detect patterns from outcomes."""

        if not self.policy_engine.should_process_event(
            LearningEventType.PATTERN_DETECTED.value,
        ):
            return []

        patterns = self.pattern_detector.detect_all_patterns(outcomes)

        if pattern_types:
            patterns = [
                pattern
                for pattern in patterns
                if pattern.get("type") in pattern_types
            ]

        results = []

        for pattern in patterns:
            requires_approval = (
                self.policy_engine.requires_approval_for_event(
                    LearningEventType.PATTERN_DETECTED.value,
                    pattern.get("confidence", 0.5),
                )
            )

            results.append(
                {
                    "pattern": pattern,
                    "requires_approval": requires_approval,
                    "can_auto_apply": not requires_approval,
                }
            )

        self.stats["patterns_detected"] += len(results)
        return results

    def generate_insights(
        self,
        patterns: list[dict[str, Any]],
        max_insights: int = 10,
    ) -> list[dict[str, Any]]:
        """Generate insights from detected patterns."""

        if not self.policy_engine.should_process_event(
            LearningEventType.INSIGHT_GENERATED.value,
        ):
            return []

        insights = self.insight_generator.generate_multiple(
            patterns,
            max_insights,
        )

        results = []

        for insight in insights:
            requires_approval = (
                self.policy_engine.requires_approval_for_event(
                    LearningEventType.INSIGHT_GENERATED.value,
                    insight.get("confidence", 0.5),
                )
            )

            results.append(
                {
                    "insight": insight,
                    "requires_approval": requires_approval,
                    "can_auto_apply": not requires_approval,
                }
            )

        self.stats["insights_generated"] += len(results)
        return results

    def propose_hypothesis(
        self,
        description: str,
        statement: str,
        confidence: float,
        evidence: dict[str, Any] | None = None,
        related_patterns: list[int] | None = None,
    ) -> dict[str, Any]:
        """Propose a new hypothesis."""

        if not self.policy_engine.should_process_event(
            LearningEventType.HYPOTHESIS_FORMED.value,
        ):
            return {"error": "Hypothesis processing is disabled"}

        requires_approval = self.policy_engine.requires_approval_for_event(
            LearningEventType.HYPOTHESIS_FORMED.value,
            confidence,
        )

        hypothesis = {
            "description": description,
            "statement": statement,
            "confidence": confidence,
            "evidence_base": evidence or {},
            "related_patterns": related_patterns or [],
            "status": "proposed",
            "requires_approval": requires_approval,
        }

        self.stats["hypotheses_proposed"] += 1
        return hypothesis

    def approve_learning(
        self,
        learning_record: LearningRecord,
        notes: str = "",
    ) -> bool:
        """Approve a learning record."""
        learning_record.approve(notes)
        self.stats["learning_records_approved"] += 1
        return True

    def reject_learning(
        self,
        learning_record: LearningRecord,
        notes: str = "",
    ) -> bool:
        """Reject a learning record."""
        learning_record.reject(notes)
        self.stats["learning_records_rejected"] += 1
        return True

    def aggregate_evidence(
        self,
        outcomes: list[Outcome],
        analysis_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Aggregate evidence from outcomes."""
        return self.evidence_aggregator.aggregate_from_outcomes(
            outcomes,
            analysis_fields,
        )

    def get_statistics(self) -> dict[str, int]:
        """Return learning statistics."""
        return self.stats.copy()

    def reset_statistics(self) -> None:
        """Reset learning statistics."""
        self.stats = self._create_statistics()

    def get_health_report(self) -> dict[str, Any]:
        """Return the health report for the learning engine."""

        total_records = (
            self.stats["learning_records_approved"]
            + self.stats["learning_records_rejected"]
        )

        approval_rate = (
            self.stats["learning_records_approved"] / total_records
            if total_records > 0
            else 0
        )

        return {
            "status": "healthy",
            "total_records_processed": total_records,
            "approval_rate": approval_rate,
            "patterns_detected": self.stats["patterns_detected"],
            "insights_generated": self.stats["insights_generated"],
            "hypotheses_proposed": self.stats["hypotheses_proposed"],
            "policy_mode": "standard",
            "timestamp": datetime.now(UTC).timestamp(),
        }