from __future__ import annotations


class ConnectorDiscoveryService:
    """Detecta plataformas conhecidas pelo nome informado."""

    def detect(self, platform_name: str) -> str:
        normalized = platform_name.lower().strip()
        if "linkedin" in normalized:
            return "linkedin"
        if "workday" in normalized:
            return "workday"
        if "smart" in normalized or "recruiters" in normalized:
            return "smartrecruiters"
        if "greenhouse" in normalized:
            return "greenhouse"
        if "lever" in normalized:
            return "lever"
        if "gupy" in normalized:
            return "gupy"
        return "unknown"
