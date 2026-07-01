"""Pattern detector for identifying patterns in application outcomes."""

from typing import Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from acd.domain.learning.pattern import Pattern, PatternType
from acd.domain.learning.outcome import Outcome, OutcomeResult
from acd.infrastructure.learning.confidence_calculator import ConfidenceCalculator


class PatternDetector:
    """Detects patterns in application and outcome data."""

    def __init__(self) -> None:
        """Initialize pattern detector."""
        self.confidence_calculator = ConfidenceCalculator()
        self.min_evidence_threshold = 5
        self.min_success_ratio = 0.6

    def detect_skill_success_pattern(
        self,
        outcomes: list[Outcome],
        min_skill_frequency: int = 3
    ) -> list[dict[str, Any]]:
        """Detect skills that correlate with success.

        Args:
            outcomes: List of outcomes to analyze
            min_skill_frequency: Minimum times skill appears

        Returns:
            List of detected patterns
        """
        skill_outcomes = defaultdict(list)

        # Group outcomes by skill
        for outcome in outcomes:
            for skill in outcome.skills_mentioned:
                skill_outcomes[skill].append(outcome)

        patterns = []

        for skill, skill_outcomes_list in skill_outcomes.items():
            if len(skill_outcomes_list) < min_skill_frequency:
                continue

            successful = sum(1 for o in skill_outcomes_list if o.is_positive())
            success_ratio = successful / len(skill_outcomes_list)

            if success_ratio >= self.min_success_ratio:
                confidence = self.confidence_calculator.calculate_combined(
                    evidence_count=len(skill_outcomes_list),
                    supporting_ratio=success_ratio,
                )

                patterns.append({
                    "type": PatternType.SKILL_SUCCESS.value,
                    "name": f"Success with {skill} skill",
                    "description": f"{skill} appears in {successful}/{len(skill_outcomes_list)} successful applications",
                    "criteria": {
                        "skill": skill,
                        "success_ratio": success_ratio,
                        "applications": len(skill_outcomes_list),
                    },
                    "evidence_count": len(skill_outcomes_list),
                    "confidence": confidence,
                    "impact": success_ratio - 0.3,  # Base success rate assumed ~30%
                    "related_outcomes": [o.id for o in skill_outcomes_list],
                })

        return patterns

    def detect_platform_conversion_pattern(
        self,
        outcomes: list[Outcome],
    ) -> list[dict[str, Any]]:
        """Detect platforms with high conversion rates.

        Args:
            outcomes: List of outcomes to analyze

        Returns:
            List of detected patterns
        """
        platform_outcomes = defaultdict(list)

        for outcome in outcomes:
            if outcome.platform:
                platform_outcomes[outcome.platform].append(outcome)

        patterns = []

        for platform, platform_outcomes_list in platform_outcomes.items():
            if len(platform_outcomes_list) < self.min_evidence_threshold:
                continue

            successful = sum(1 for o in platform_outcomes_list if o.is_positive())
            conversion_rate = successful / len(platform_outcomes_list)

            confidence = self.confidence_calculator.calculate_combined(
                evidence_count=len(platform_outcomes_list),
                supporting_ratio=conversion_rate,
            )

            patterns.append({
                "type": PatternType.PLATFORM_SUCCESS.value,
                "name": f"High conversion on {platform}",
                "description": f"{platform} has {conversion_rate*100:.1f}% success rate",
                "criteria": {
                    "platform": platform,
                    "min_conversion": conversion_rate,
                    "applications": len(platform_outcomes_list),
                },
                "evidence_count": len(platform_outcomes_list),
                "confidence": confidence,
                "impact": conversion_rate - 0.3,
                "related_outcomes": [o.id for o in platform_outcomes_list],
            })

        return patterns

    def detect_sector_pattern(
        self,
        outcomes: list[Outcome],
    ) -> list[dict[str, Any]]:
        """Detect sectors with high success rates.

        Args:
            outcomes: List of outcomes to analyze

        Returns:
            List of detected patterns
        """
        sector_outcomes = defaultdict(list)

        for outcome in outcomes:
            if outcome.sector:
                sector_outcomes[outcome.sector].append(outcome)

        patterns = []

        for sector, sector_outcomes_list in sector_outcomes.items():
            if len(sector_outcomes_list) < self.min_evidence_threshold:
                continue

            successful = sum(1 for o in sector_outcomes_list if o.is_positive())
            success_rate = successful / len(sector_outcomes_list)

            confidence = self.confidence_calculator.calculate_combined(
                evidence_count=len(sector_outcomes_list),
                supporting_ratio=success_rate,
            )

            patterns.append({
                "type": PatternType.SECTOR_PATTERN.value,
                "name": f"Strong results in {sector}",
                "description": f"{sector} sector shows {success_rate*100:.1f}% success",
                "criteria": {
                    "sector": sector,
                    "min_success_rate": success_rate,
                    "applications": len(sector_outcomes_list),
                },
                "evidence_count": len(sector_outcomes_list),
                "confidence": confidence,
                "impact": success_rate - 0.3,
                "related_outcomes": [o.id for o in sector_outcomes_list],
            })

        return patterns

    def detect_timing_pattern(
        self,
        outcomes: list[Outcome],
        days_window: int = 7,
    ) -> list[dict[str, Any]]:
        """Detect day/time patterns for better response rates.

        Args:
            outcomes: List of outcomes to analyze
            days_window: Window size for grouping

        Returns:
            List of detected patterns
        """
        day_outcomes = defaultdict(list)

        for outcome in outcomes:
            day_of_week = outcome.recorded_date.weekday()  # 0=Monday
            day_outcomes[day_of_week].append(outcome)

        patterns = []

        for day_of_week, day_outcomes_list in day_outcomes.items():
            if len(day_outcomes_list) < self.min_evidence_threshold:
                continue

            successful = sum(1 for o in day_outcomes_list if o.is_positive())
            success_rate = successful / len(day_outcomes_list)

            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_name = day_names[day_of_week]

            confidence = self.confidence_calculator.calculate_combined(
                evidence_count=len(day_outcomes_list),
                supporting_ratio=success_rate,
            )

            patterns.append({
                "type": PatternType.TIMING_PATTERN.value,
                "name": f"Better results on {day_name}",
                "description": f"Applications submitted on {day_name} show {success_rate*100:.1f}% success",
                "criteria": {
                    "day_of_week": day_of_week,
                    "day_name": day_name,
                    "success_rate": success_rate,
                },
                "evidence_count": len(day_outcomes_list),
                "confidence": confidence,
                "impact": success_rate - 0.3,
                "related_outcomes": [o.id for o in day_outcomes_list],
            })

        return patterns

    def detect_resume_type_pattern(
        self,
        outcomes: list[Outcome],
        min_resume_usage: int = 3,
    ) -> list[dict[str, Any]]:
        """Detect which resume versions perform best.

        Args:
            outcomes: List of outcomes to analyze
            min_resume_usage: Minimum times resume appears

        Returns:
            List of detected patterns
        """
        resume_outcomes = defaultdict(list)

        for outcome in outcomes:
            if outcome.curriculum_id:
                resume_outcomes[outcome.curriculum_id].append(outcome)

        patterns = []

        for resume_id, resume_outcomes_list in resume_outcomes.items():
            if len(resume_outcomes_list) < min_resume_usage:
                continue

            successful = sum(1 for o in resume_outcomes_list if o.is_positive())
            success_rate = successful / len(resume_outcomes_list)

            confidence = self.confidence_calculator.calculate_combined(
                evidence_count=len(resume_outcomes_list),
                supporting_ratio=success_rate,
            )

            patterns.append({
                "type": PatternType.RESUME_TYPE_SUCCESS.value,
                "name": f"High-performing resume (ID: {resume_id})",
                "description": f"Resume {resume_id} achieves {success_rate*100:.1f}% success rate",
                "criteria": {
                    "resume_id": resume_id,
                    "success_rate": success_rate,
                    "applications": len(resume_outcomes_list),
                },
                "evidence_count": len(resume_outcomes_list),
                "confidence": confidence,
                "impact": success_rate - 0.3,
                "related_outcomes": [o.id for o in resume_outcomes_list],
            })

        return patterns

    def detect_all_patterns(self, outcomes: list[Outcome]) -> list[dict[str, Any]]:
        """Detect all available patterns.

        Args:
            outcomes: List of outcomes to analyze

        Returns:
            List of all detected patterns
        """
        all_patterns = []

        all_patterns.extend(self.detect_skill_success_pattern(outcomes))
        all_patterns.extend(self.detect_platform_conversion_pattern(outcomes))
        all_patterns.extend(self.detect_sector_pattern(outcomes))
        all_patterns.extend(self.detect_timing_pattern(outcomes))
        all_patterns.extend(self.detect_resume_type_pattern(outcomes))

        return all_patterns
