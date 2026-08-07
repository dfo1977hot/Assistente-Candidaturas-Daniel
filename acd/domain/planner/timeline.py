from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Timeline:
    """
    Cronograma sugerido pelo Planner.
    """

    apply_today: bool = True

    followup_days: int = 7

    expected_response_days: int = 15
