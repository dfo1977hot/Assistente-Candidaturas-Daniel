from __future__ import annotations

from acd.services.knowledge_service import KnowledgeService


def create_skill(
    service: KnowledgeService,
    *,
    name: str,
    category: str = "",
    description: str = "",
    weight: float = 0.0,
):
    """Aplicação para cadastro de competência."""
    return service.create_skill(
        name=name, category=category, description=description, weight=weight
    )
