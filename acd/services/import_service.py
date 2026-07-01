from __future__ import annotations

from typing import Any

from acd.services.profile_service import ProfileService


class ImportService:
    """Importa dados de fontes externas como LinkedIn."""

    def __init__(self, profile_service: ProfileService | None = None) -> None:
        self.profile_service = profile_service or ProfileService()

    def import_data(self, payload: dict[str, Any], *, source: str) -> dict[str, Any]:
        profile = self.profile_service.create_profile(
            full_name=payload.get("full_name", ""),
            email=payload.get("email", ""),
        )
        if source == "linkedin" and payload.get("experiences"):
            self.profile_service.update_profile(profile.id, summary="Importado do LinkedIn")
        return {"profile_id": profile.id, "source": source, "status": "imported"}
