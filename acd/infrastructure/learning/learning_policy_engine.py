"""Learning policy engine for configuring learning behaviors."""

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ApprovalRequirement(StrEnum):
    """Approval requirements for learning."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"
    CONDITIONAL = "conditional"  # Requires approval if confidence < threshold


class LearningEventType(StrEnum):
    """Types of learning events."""

    OUTCOME_RECORDED = "outcome_recorded"
    PATTERN_DETECTED = "pattern_detected"
    INSIGHT_GENERATED = "insight_generated"
    HYPOTHESIS_FORMED = "hypothesis_formed"
    CONFIDENCE_THRESHOLD_MET = "confidence_threshold_met"


@dataclass
class LearningPolicy:
    """Policy for handling a specific learning event type."""

    event_type: str
    enabled: bool = True
    approval_required: str = ApprovalRequirement.MANUAL.value
    confidence_threshold: float = 0.7
    evidence_threshold: int = 5
    auto_apply: bool = False
    max_recommendations_per_type: int = 10
    retention_days: int | None = None  # None = keep forever
    metadata: dict[str, Any] = field(default_factory=dict)

    def requires_approval(self, confidence: float) -> bool:
        """Check if approval is required.

        Args:
            confidence: Confidence level

        Returns:
            True if approval required
        """
        if self.approval_required == ApprovalRequirement.AUTOMATIC.value:
            return False
        elif self.approval_required == ApprovalRequirement.MANUAL.value:
            return True
        elif self.approval_required == ApprovalRequirement.CONDITIONAL.value:
            return confidence < self.confidence_threshold
        return False

    def can_auto_apply(self, confidence: float, evidence_count: int) -> bool:
        """Check if learning can be auto-applied.

        Args:
            confidence: Confidence level
            evidence_count: Number of evidence items

        Returns:
            True if can auto-apply
        """
        return (
            self.auto_apply
            and confidence >= self.confidence_threshold
            and evidence_count >= self.evidence_threshold
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class LearningPolicyEngine:
    """Configures and manages learning policies."""

    def __init__(self) -> None:
        """Initialize policy engine."""
        self.policies: dict[str, LearningPolicy] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self) -> None:
        """Initialize default policies."""
        # Outcomes require manual approval but low evidence threshold
        self.policies[LearningEventType.OUTCOME_RECORDED.value] = LearningPolicy(
            event_type=LearningEventType.OUTCOME_RECORDED.value,
            enabled=True,
            approval_required=ApprovalRequirement.MANUAL.value,
            confidence_threshold=0.5,
            evidence_threshold=1,
            auto_apply=False,
        )

        # Patterns require approval at lower confidence
        self.policies[LearningEventType.PATTERN_DETECTED.value] = LearningPolicy(
            event_type=LearningEventType.PATTERN_DETECTED.value,
            enabled=True,
            approval_required=ApprovalRequirement.CONDITIONAL.value,
            confidence_threshold=0.75,
            evidence_threshold=5,
            auto_apply=False,
        )

        # Insights require conditional approval
        self.policies[LearningEventType.INSIGHT_GENERATED.value] = LearningPolicy(
            event_type=LearningEventType.INSIGHT_GENERATED.value,
            enabled=True,
            approval_required=ApprovalRequirement.CONDITIONAL.value,
            confidence_threshold=0.8,
            evidence_threshold=10,
            auto_apply=False,
            max_recommendations_per_type=5,
        )

        # Hypotheses always require manual approval
        self.policies[LearningEventType.HYPOTHESIS_FORMED.value] = LearningPolicy(
            event_type=LearningEventType.HYPOTHESIS_FORMED.value,
            enabled=True,
            approval_required=ApprovalRequirement.MANUAL.value,
            confidence_threshold=0.6,
            evidence_threshold=3,
            auto_apply=False,
        )

        # High confidence items can potentially auto-apply
        self.policies[LearningEventType.CONFIDENCE_THRESHOLD_MET.value] = LearningPolicy(
            event_type=LearningEventType.CONFIDENCE_THRESHOLD_MET.value,
            enabled=True,
            approval_required=ApprovalRequirement.CONDITIONAL.value,
            confidence_threshold=0.9,
            evidence_threshold=20,
            auto_apply=False,
        )

    def get_policy(self, event_type: str) -> LearningPolicy | None:
        """Get policy for event type.

        Args:
            event_type: Event type

        Returns:
            Policy or None
        """
        return self.policies.get(event_type)

    def set_policy(self, event_type: str, policy: LearningPolicy) -> None:
        """Set policy for event type.

        Args:
            event_type: Event type
            policy: Policy to set
        """
        self.policies[event_type] = policy

    def should_process_event(self, event_type: str) -> bool:
        """Check if event should be processed.

        Args:
            event_type: Event type

        Returns:
            True if event should be processed
        """
        policy = self.get_policy(event_type)
        return policy.enabled if policy else True

    def requires_approval_for_event(
        self,
        event_type: str,
        confidence: float,
    ) -> bool:
        """Check if approval required for event.

        Args:
            event_type: Event type
            confidence: Confidence level

        Returns:
            True if approval required
        """
        policy = self.get_policy(event_type)
        if not policy:
            return True  # Default to requiring approval
        return policy.requires_approval(confidence)

    def can_auto_apply_learning(
        self,
        event_type: str,
        confidence: float,
        evidence_count: int,
    ) -> bool:
        """Check if learning can be auto-applied.

        Args:
            event_type: Event type
            confidence: Confidence level
            evidence_count: Evidence count

        Returns:
            True if can auto-apply
        """
        policy = self.get_policy(event_type)
        if not policy:
            return False
        return policy.can_auto_apply(confidence, evidence_count)

    def get_all_policies(self) -> dict[str, dict[str, Any]]:
        """Get all policies as dictionaries.

        Returns:
            All policies
        """
        return {event_type: policy.to_dict() for event_type, policy in self.policies.items()}

    def configure_auto_approval_mode(self, enabled: bool) -> None:
        """Configure automatic approval mode.

        Args:
            enabled: Enable auto approval mode
        """
        for policy in self.policies.values():
            if enabled:
                policy.approval_required = ApprovalRequirement.CONDITIONAL.value
                policy.confidence_threshold = 0.85
            else:
                policy.approval_required = ApprovalRequirement.MANUAL.value

    def configure_strict_mode(self, enabled: bool) -> None:
        """Configure strict approval mode.

        Args:
            enabled: Enable strict mode
        """
        for policy in self.policies.values():
            if enabled:
                policy.approval_required = ApprovalRequirement.MANUAL.value
                policy.confidence_threshold = 0.95
                policy.evidence_threshold = max(policy.evidence_threshold, 50)
            else:
                policy.approval_required = ApprovalRequirement.CONDITIONAL.value
                policy.confidence_threshold = 0.7
                policy.evidence_threshold = max(5, policy.evidence_threshold // 2)
