from __future__ import annotations

import json
from typing import Any


class ExportService:
    """Exporta dados de perfil em formatos simples."""

    def export_data(self, payload: dict[str, Any], *, format: str) -> str:
        if format == "json":
            return json.dumps(payload)
        return json.dumps(payload)
