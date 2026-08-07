from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SalarySuggestion:
    """
    Faixa salarial recomendada.
    """

    minimum: float

    recommended: float

    maximum: float

    currency: str = "BRL"
