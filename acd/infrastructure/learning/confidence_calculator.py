"""Confidence calculator for assigning confidence levels to hypotheses and patterns."""


class ConfidenceCalculator:
    """Calculates confidence levels based on evidence quality and quantity."""

    def __init__(self) -> None:
        """Initialize calculator."""
        self.min_evidence_for_high_confidence = 50
        self.min_evidence_for_medium_confidence = 20
        self.min_evidence_for_low_confidence = 5

    def calculate_from_evidence_count(
        self, evidence_count: int, base_confidence: float = 0.5
    ) -> float:
        """Calculate confidence based on evidence count.

        Args:
            evidence_count: Number of evidence items
            base_confidence: Base confidence to adjust

        Returns:
            Confidence level (0-1)
        """
        if evidence_count >= self.min_evidence_for_high_confidence:
            adjustment = 0.3
        elif evidence_count >= self.min_evidence_for_medium_confidence:
            adjustment = 0.2
        elif evidence_count >= self.min_evidence_for_low_confidence:
            adjustment = 0.1
        else:
            adjustment = -0.1

        confidence = base_confidence + adjustment
        return max(0.0, min(1.0, confidence))

    def calculate_from_consistency(
        self, supporting_count: int, total_count: int, min_threshold: float = 0.6
    ) -> float:
        """Calculate confidence from consistency ratio.

        Args:
            supporting_count: Count of supporting evidence
            total_count: Total count of evidence
            min_threshold: Minimum threshold for consistency

        Returns:
            Confidence level (0-1)
        """
        if total_count == 0:
            return 0.0

        consistency = supporting_count / total_count
        if consistency >= min_threshold:
            return min(0.95, consistency + 0.1)
        else:
            return consistency * 0.8

    def calculate_combined(
        self,
        evidence_count: int,
        supporting_ratio: float,
        data_recency_days: int = 0,
        expert_adjustment: float = 0.0,
    ) -> float:
        """Calculate confidence from multiple factors.

        Args:
            evidence_count: Number of evidence items
            supporting_ratio: Ratio of supporting to total evidence
            data_recency_days: Days since data collection (0=today)
            expert_adjustment: Manual expert adjustment (-0.2 to 0.2)

        Returns:
            Confidence level (0-1)
        """
        # Base confidence from consistency
        base = self.calculate_from_consistency(
            int(supporting_ratio * evidence_count), evidence_count
        )

        # Adjust for evidence count
        count_adjustment = min(0.15, evidence_count / 100)
        base += count_adjustment

        # Decay for old data (5% per week)
        recency_decay = max(0, (data_recency_days / 7) * 0.05)
        base -= recency_decay

        # Apply expert adjustment
        base += expert_adjustment

        return max(0.0, min(1.0, base))

    def get_confidence_label(self, confidence: float) -> str:
        """Get human-readable confidence label.

        Args:
            confidence: Confidence value (0-1)

        Returns:
            Label (Very Low, Low, Medium, High, Very High)
        """
        if confidence >= 0.9:
            return "Very High"
        elif confidence >= 0.75:
            return "High"
        elif confidence >= 0.5:
            return "Medium"
        elif confidence >= 0.25:
            return "Low"
        else:
            return "Very Low"

    def calculate_data_quality_score(
        self,
        completeness: float,  # 0-1: How complete is the data
        accuracy: float,  # 0-1: How accurate
        timeliness: float,  # 0-1: How recent
        representativeness: float = 1.0,  # 0-1: How representative
    ) -> float:
        """Calculate overall data quality score.

        Args:
            completeness: Data completeness ratio
            accuracy: Data accuracy ratio
            timeliness: Data timeliness ratio (1 = today, 0 = >6 months old)
            representativeness: Sample representativeness

        Returns:
            Quality score (0-1)
        """
        weights = {
            "completeness": 0.3,
            "accuracy": 0.35,
            "timeliness": 0.25,
            "representativeness": 0.1,
        }

        quality = (
            completeness * weights["completeness"]
            + accuracy * weights["accuracy"]
            + timeliness * weights["timeliness"]
            + representativeness * weights["representativeness"]
        )

        return max(0.0, min(1.0, quality))
