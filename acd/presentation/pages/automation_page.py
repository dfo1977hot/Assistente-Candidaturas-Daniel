from __future__ import annotations

from acd.presentation.pages.base_page import BasePage


class AutomationPage(BasePage):
    """Página de automação de candidaturas."""

    def __init__(self) -> None:
        super().__init__("Automações")
