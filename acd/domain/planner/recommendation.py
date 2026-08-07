from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Recommendation:
    """
    Recomendação produzida pelo Planner.
    """

    title: str

    description: str

    importance: int = 1
