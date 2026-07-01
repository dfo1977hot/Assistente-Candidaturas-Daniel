from __future__ import annotations

from acd.presentation.pages.base_page import BasePage
from acd.services.ats_service import ATSService


class ATSPage(BasePage):
    """Página de cálculo do ATS Score."""

    def __init__(self, service: ATSService | None = None) -> None:
        super().__init__("ATS Score")
        self.service = service or ATSService()
