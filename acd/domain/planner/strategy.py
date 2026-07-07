from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Strategy:
    """
    Estratégia recomendada para a candidatura.
    """

    title: str

    description: str

    rationale: str
