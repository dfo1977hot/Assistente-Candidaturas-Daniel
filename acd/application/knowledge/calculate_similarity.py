from __future__ import annotations

from acd.services.knowledge_service import KnowledgeService


def calculate_similarity(service: KnowledgeService, left: str, right: str) -> float:
    """Aplicação para calcular similaridade entre competências."""
    return service.calculate_similarity(left, right)
