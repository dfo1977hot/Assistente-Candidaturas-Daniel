from __future__ import annotations

from acd.domain.entities.skill import Skill
from acd.services.knowledge_service import KnowledgeService


def search_skill(service: KnowledgeService, query: str) -> list[Skill]:
    """Aplicação para buscar competências."""
    return service.search_skills(query)
