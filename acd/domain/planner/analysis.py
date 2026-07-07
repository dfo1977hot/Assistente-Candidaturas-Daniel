from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Analysis:
    """
    Resultado de uma análise individual.
    """

    name: str

    score: float

    weight: float

    observation: str = ""
