from __future__ import annotations

from acd.presentation.pages.base_page import BasePage


class AIGenerationDialog(BasePage):
    """Diálogo base para geração assistida por IA."""

    def __init__(self) -> None:
        super().__init__("Geração IA")
