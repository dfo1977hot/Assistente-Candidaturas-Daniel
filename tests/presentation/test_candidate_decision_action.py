"""Tests for Candidate Decision navigation actions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from acd.presentation.models.candidate_decision_action import CandidateDecisionAction


def test_candidate_decision_action_is_immutable_descriptor() -> None:
    action = CandidateDecisionAction("review_gaps", "Revisar gaps", "Abrir lacunas.", True)

    assert action.id == "review_gaps"
    assert action.label == "Revisar gaps"
    assert action.description == "Abrir lacunas."
    assert action.enabled is True
    with pytest.raises(FrozenInstanceError):
        action.enabled = False
