from __future__ import annotations

from acd.services.ats_service import ATSService


def explain_score(
    service: ATSService, *, total_score: int, criteria: dict[str, dict[str, float]]
) -> dict[str, object]:
    """Aplicação para explicar o score calculado."""
    return service.explanation_engine.build(total_score=total_score, criteria=criteria)
