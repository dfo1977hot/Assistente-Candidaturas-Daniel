"""Adapters for exposing existing ATS results as ACL contracts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from acd.application.composition.read_models import ATSContext, GapContext
from acd.application.query_ports import ATSHistoryQueryDTO


class ATSContextAdapter:
    """Transforms the existing ATS result shape into reusable read models."""

    def to_ats_context(self, result: Mapping[str, Any]) -> ATSContext:
        """Create an ATS context without modifying the original result."""
        explanation = result.get("explanation")
        details = explanation if isinstance(explanation, Mapping) else None
        return ATSContext(
            total_score=float(result["total_score"]),
            recommendations=tuple(str(item) for item in result.get("recommendations", ())),
            details=details,
        )

    def from_history(self, history: ATSHistoryQueryDTO) -> ATSContext:
        """Create an ATS context from a persisted ATS history DTO."""
        details = (
            None
            if history.score_details is None
            else {
                detail.criterion: {
                    "score": detail.score,
                    "max_score": detail.max_score,
                    "weight": detail.weight,
                }
                for detail in history.score_details
            }
        )
        return ATSContext(
            total_score=history.total_score,
            recommendations=(
                ()
                if history.recommendations is None
                else tuple(recommendation.message for recommendation in history.recommendations)
            ),
            details=details,
        )

    def gap_context_from_history(self, history: ATSHistoryQueryDTO) -> GapContext | None:
        """Project persisted ATS gaps without re-running the ATS analysis."""
        if history.gaps is None:
            return None
        return GapContext(
            missing_skills=tuple(
                gap.skill_name for gap in history.gaps if gap.gap_type == "missing"
            ),
            desired_skills=tuple(
                gap.skill_name for gap in history.gaps if gap.gap_type != "missing"
            ),
        )

    def to_gap_context(self, result: Mapping[str, Any]) -> GapContext:
        """Create a gap context from the existing ATS gap result."""
        gaps = result.get("gaps", {})
        if not isinstance(gaps, Mapping):
            raise ValueError("ATS result gaps must be a mapping.")
        return GapContext(
            missing_skills=tuple(str(item) for item in gaps.get("missing_skills", ())),
            desired_skills=tuple(str(item) for item in gaps.get("desired_skills", ())),
        )
