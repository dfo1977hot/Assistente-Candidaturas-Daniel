from __future__ import annotations

import pytest

from acd.application.composition.ats_context_adapter import ATSContextAdapter


def test_ats_context_adapter_creates_reusable_ats_and_gap_contexts() -> None:
    """Existing ATS output is represented without exposing its dictionary shape."""
    result = {
        "total_score": 81.5,
        "recommendations": ["Destacar Python."],
        "gaps": {"missing_skills": ["Docker"], "desired_skills": ["Kubernetes"]},
        "explanation": {"details": [{"label": "Competências"}]},
    }

    adapter = ATSContextAdapter()

    assert adapter.to_ats_context(result).total_score == 81.5
    assert adapter.to_gap_context(result).missing_skills == ("Docker",)


def test_ats_context_adapter_rejects_an_invalid_gap_shape() -> None:
    """Only ATS results with a mapping of gaps can produce a gap context."""
    with pytest.raises(ValueError, match="gaps"):
        ATSContextAdapter().to_gap_context({"total_score": 1.0, "gaps": []})
