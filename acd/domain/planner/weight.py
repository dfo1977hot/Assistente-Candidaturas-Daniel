from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Weight:
    """
    Representa o peso de um critério de análise.

    Valor válido entre 0.0 e 1.0.
    """

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Weight must be between 0.0 and 1.0.")
