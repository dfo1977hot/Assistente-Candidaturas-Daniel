"""Evidence aggregator for consolidating evidence from multiple sources."""

from collections import defaultdict
from typing import Any


class EvidenceAggregator:
    """Aggregates evidence from multiple sources for pattern detection."""

    def __init__(self) -> None:
        """Initialize aggregator."""
        self.evidence_sources = {}

    def add_evidence_source(self, source_name: str, extractor_fn) -> None:
        """Add an evidence source.

        Args:
            source_name: Name of the source
            extractor_fn: Function to extract evidence from source
        """
        self.evidence_sources[source_name] = extractor_fn

    def aggregate_from_outcomes(
        self,
        outcomes: list[Any],
        analysis_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Aggregate evidence from outcomes.

        Args:
            outcomes: List of outcome objects
            analysis_fields: Fields to analyze

        Returns:
            Aggregated evidence
        """
        if analysis_fields is None:
            analysis_fields = [
                "skills_mentioned",
                "platform",
                "sector",
                "recorded_date",
                "curriculum_id",
                "result",
            ]

        aggregated = {
            "total_outcomes": len(outcomes),
            "successful_outcomes": sum(
                1 for o in outcomes if hasattr(o, "is_positive") and o.is_positive()
            ),
            "failed_outcomes": sum(
                1 for o in outcomes if hasattr(o, "is_positive") and o.is_negative()
            ),
            "success_rate": 0.0,
            "evidence_by_field": defaultdict(dict),
            "time_range": self._get_time_range(outcomes),
            "details": {},
        }

        if aggregated["total_outcomes"] > 0:
            aggregated["success_rate"] = (
                aggregated["successful_outcomes"] / aggregated["total_outcomes"]
            )

        # Analyze specific fields
        for field in analysis_fields:
            if field == "skills_mentioned":
                aggregated["details"][field] = self._aggregate_skills(outcomes)
            elif field == "platform":
                aggregated["details"][field] = self._aggregate_platforms(outcomes)
            elif field == "sector":
                aggregated["details"][field] = self._aggregate_sectors(outcomes)
            elif field == "recorded_date":
                aggregated["details"][field] = self._aggregate_dates(outcomes)
            elif field == "curriculum_id":
                aggregated["details"][field] = self._aggregate_resumes(outcomes)

        return aggregated

    def _aggregate_skills(self, outcomes: list[Any]) -> dict[str, Any]:
        """Aggregate skill evidence.

        Args:
            outcomes: List of outcomes

        Returns:
            Skill aggregation
        """
        skill_success = defaultdict(lambda: {"success": 0, "total": 0})

        for outcome in outcomes:
            if hasattr(outcome, "skills_mentioned"):
                for skill in outcome.skills_mentioned:
                    skill_success[skill]["total"] += 1
                    if hasattr(outcome, "is_positive") and outcome.is_positive():
                        skill_success[skill]["success"] += 1

        return {
            skill: {
                "count": data["total"],
                "success_count": data["success"],
                "success_rate": data["success"] / data["total"] if data["total"] > 0 else 0,
            }
            for skill, data in skill_success.items()
        }

    def _aggregate_platforms(self, outcomes: list[Any]) -> dict[str, Any]:
        """Aggregate platform evidence.

        Args:
            outcomes: List of outcomes

        Returns:
            Platform aggregation
        """
        platform_success = defaultdict(lambda: {"success": 0, "total": 0})

        for outcome in outcomes:
            if hasattr(outcome, "platform") and outcome.platform:
                platform_success[outcome.platform]["total"] += 1
                if hasattr(outcome, "is_positive") and outcome.is_positive():
                    platform_success[outcome.platform]["success"] += 1

        return {
            platform: {
                "count": data["total"],
                "success_count": data["success"],
                "success_rate": data["success"] / data["total"] if data["total"] > 0 else 0,
            }
            for platform, data in platform_success.items()
        }

    def _aggregate_sectors(self, outcomes: list[Any]) -> dict[str, Any]:
        """Aggregate sector evidence.

        Args:
            outcomes: List of outcomes

        Returns:
            Sector aggregation
        """
        sector_success = defaultdict(lambda: {"success": 0, "total": 0})

        for outcome in outcomes:
            if hasattr(outcome, "sector") and outcome.sector:
                sector_success[outcome.sector]["total"] += 1
                if hasattr(outcome, "is_positive") and outcome.is_positive():
                    sector_success[outcome.sector]["success"] += 1

        return {
            sector: {
                "count": data["total"],
                "success_count": data["success"],
                "success_rate": data["success"] / data["total"] if data["total"] > 0 else 0,
            }
            for sector, data in sector_success.items()
        }

    def _aggregate_dates(self, outcomes: list[Any]) -> dict[str, Any]:
        """Aggregate date evidence.

        Args:
            outcomes: List of outcomes

        Returns:
            Date aggregation
        """
        date_success = defaultdict(lambda: {"success": 0, "total": 0})

        for outcome in outcomes:
            if hasattr(outcome, "recorded_date"):
                date_key = outcome.recorded_date.strftime("%Y-%m-%d")
                date_success[date_key]["total"] += 1
                if hasattr(outcome, "is_positive") and outcome.is_positive():
                    date_success[date_key]["success"] += 1

        return {
            date: {
                "count": data["total"],
                "success_count": data["success"],
                "success_rate": data["success"] / data["total"] if data["total"] > 0 else 0,
            }
            for date, data in date_success.items()
        }

    def _aggregate_resumes(self, outcomes: list[Any]) -> dict[str, Any]:
        """Aggregate resume evidence.

        Args:
            outcomes: List of outcomes

        Returns:
            Resume aggregation
        """
        resume_success = defaultdict(lambda: {"success": 0, "total": 0})

        for outcome in outcomes:
            if hasattr(outcome, "curriculum_id") and outcome.curriculum_id:
                resume_id = str(outcome.curriculum_id)
                resume_success[resume_id]["total"] += 1
                if hasattr(outcome, "is_positive") and outcome.is_positive():
                    resume_success[resume_id]["success"] += 1

        return {
            resume_id: {
                "count": data["total"],
                "success_count": data["success"],
                "success_rate": data["success"] / data["total"] if data["total"] > 0 else 0,
            }
            for resume_id, data in resume_success.items()
        }

    def _get_time_range(self, outcomes: list[Any]) -> dict[str, Any]:
        """Get time range of outcomes.

        Args:
            outcomes: List of outcomes

        Returns:
            Time range information
        """
        if not outcomes:
            return {"start": None, "end": None, "days": 0}

        dates = []
        for outcome in outcomes:
            if hasattr(outcome, "recorded_date"):
                dates.append(outcome.recorded_date)

        if not dates:
            return {"start": None, "end": None, "days": 0}

        start = min(dates)
        end = max(dates)
        days = (end - start).days

        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "days": days,
        }

    def calculate_coverage(self, aggregated_evidence: dict[str, Any]) -> dict[str, float]:
        """Calculate coverage metrics.

        Args:
            aggregated_evidence: Aggregated evidence dictionary

        Returns:
            Coverage percentages
        """
        total = aggregated_evidence.get("total_outcomes", 0)
        if total == 0:
            return {}

        coverage = {}
        for field, details in aggregated_evidence.get("details", {}).items():
            non_null_count = len(details) if isinstance(details, dict) else 0
            coverage[field] = non_null_count / total if total > 0 else 0

        return coverage
