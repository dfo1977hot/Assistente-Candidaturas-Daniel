from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JobAnalysisResult:
    """
    Resultado inicial da análise de uma vaga.

    Esta versão contém apenas estatísticas básicas.
    Futuramente será enriquecida com IA.
    """

    total_words: int
    unique_words: int
    estimated_level: str