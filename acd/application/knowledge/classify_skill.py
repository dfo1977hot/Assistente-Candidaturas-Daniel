from __future__ import annotations

from acd.services.knowledge_service import KnowledgeService


def classify_skill(service: KnowledgeService, skill_name: str) -> str:
    """Aplicação para classificar uma competência."""
    return service.classify_skill(skill_name)
