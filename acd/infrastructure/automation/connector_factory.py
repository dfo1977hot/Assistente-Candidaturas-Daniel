from __future__ import annotations

from acd.infrastructure.automation.connectors import LinkedInConnector, SmartRecruitersConnector


class ConnectorFactory:
    """Cria conectores de recrutamento com base no nome da plataforma."""

    def create(self, platform: str) -> object | None:
        normalized = platform.lower().strip()
        if normalized in {"smartrecruiters", "smart recruiters"}:
            return SmartRecruitersConnector()
        if normalized in {"linkedin", "linkedin easy apply"}:
            return LinkedInConnector()
        return None
