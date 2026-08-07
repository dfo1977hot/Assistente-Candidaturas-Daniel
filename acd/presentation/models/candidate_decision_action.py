"""Immutable action descriptor for Candidate Decision Presentation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateDecisionAction:
    """Describe a user-initiated navigation action without business behavior."""

    id: str
    label: str
    description: str
    enabled: bool
