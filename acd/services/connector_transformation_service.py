from __future__ import annotations

import re


class TransformationService:
    """Aplica transformações básicas para normalizar valores."""

    def apply(self, field_name: str, value: str) -> str:
        normalized = str(value).strip()
        if field_name == "phone":
            return re.sub(r"\s+", " ", normalized)
        if field_name == "date":
            return normalized
        return normalized
