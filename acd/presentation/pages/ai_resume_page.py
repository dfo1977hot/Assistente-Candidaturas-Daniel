from __future__ import annotations

from acd.presentation.pages.base_page import BasePage


class AIResumePage(BasePage):
    """Página inicial do assistente IA para geração de currículo e carta."""

    def __init__(self) -> None:
        super().__init__("Assistente IA")
