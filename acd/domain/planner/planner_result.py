from __future__ import annotations

from dataclasses import dataclass, field

from acd.domain.planner.enums import StrategyType
from acd.domain.planner.priority import Priority
from acd.domain.planner.recommendation import Recommendation


@dataclass(slots=True)
class PlannerResult:
    """
    Resultado consolidado do processo de planejamento.

    Este objeto agrega todas as decisões produzidas pelo Planner
    após analisar uma candidatura.
    """

    # ------------------------------------------------------------------
    # Scores
    # ------------------------------------------------------------------

    adherence_score: float = 0.0
    ats_score: float = 0.0
    market_score: float = 0.0
    career_score: float = 0.0
    overall_score: float = 0.0

    # ------------------------------------------------------------------
    # Documentos recomendados
    # ------------------------------------------------------------------

    recommended_resume: str = ""
    recommended_cover_letter: str = ""

    # ------------------------------------------------------------------
    # Decisões do Planner
    # ------------------------------------------------------------------

    priority: Priority = Priority.NORMAL

    strategy: StrategyType | None = None

    salary_suggestion: float | None = None

    followup_days: int = 7

    # ------------------------------------------------------------------
    # Informações auxiliares
    # ------------------------------------------------------------------

    missing_keywords: list[str] = field(default_factory=list)

    recommendations: list[Recommendation] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)
