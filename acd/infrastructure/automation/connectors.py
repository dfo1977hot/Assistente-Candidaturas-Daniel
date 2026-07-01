from __future__ import annotations

from acd.domain.automation.connector import Connector
from acd.domain.automation.application_result import ApplicationResult


class MockConnector:
    """Conector mock para ambiente de teste e desenvolvimento."""

    def __init__(self, *, platform: str = "smartrecruiters") -> None:
        self.platform = platform

    def login(self) -> bool:
        return True

    def open_job(self, url: str) -> bool:
        return bool(url)

    def fill_form(self) -> bool:
        return True

    def upload_resume(self, path: str) -> bool:
        return bool(path)

    def upload_cover_letter(self, path: str) -> bool:
        return bool(path)

    def submit(self) -> bool:
        return True

    def capture_result(self) -> dict[str, object]:
        return {"status": "success", "message": f"{self.platform} completed"}

    def close(self) -> None:
        return None


class SmartRecruitersConnector(MockConnector):
    """Conector de referência para SmartRecruiters."""

    def __init__(self) -> None:
        super().__init__(platform="smartrecruiters")


class LinkedInConnector(MockConnector):
    """Conector de referência para LinkedIn Easy Apply."""

    def __init__(self) -> None:
        super().__init__(platform="linkedin")
