from __future__ import annotations

from enum import StrEnum


class Priority(StrEnum):
    """
    Prioridade sugerida para uma candidatura.
    """

    LOW = "Baixa"
    NORMAL = "Normal"
    HIGH = "Alta"
    CRITICAL = "Crítica"
