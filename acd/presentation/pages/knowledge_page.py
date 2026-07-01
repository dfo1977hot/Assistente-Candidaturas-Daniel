from __future__ import annotations

from acd.presentation.pages.base_page import BasePage
from acd.services.knowledge_service import KnowledgeService


class KnowledgePage(BasePage):
    """Página de cadastro e consulta do catálogo de competências."""

    def __init__(self, service: KnowledgeService | None = None) -> None:
        super().__init__("Conhecimento")
        self.service = service or KnowledgeService()
