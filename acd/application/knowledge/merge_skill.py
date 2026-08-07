from __future__ import annotations

from acd.services.knowledge_service import KnowledgeService


def merge_skill(
    service: KnowledgeService, *, source_skill_id: int, target_skill_id: int, alias_name: str
):
    """Aplicação para fusão de competências com alias."""
    return service.merge_skill(
        source_skill_id=source_skill_id, target_skill_id=target_skill_id, alias_name=alias_name
    )
