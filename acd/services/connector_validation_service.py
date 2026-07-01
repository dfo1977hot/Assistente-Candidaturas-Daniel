from __future__ import annotations

import re
from typing import Any


class ValidationService:
    """Valida campos obrigatórios e formatos básicos."""

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        if not payload.get("required"):
            errors.append("required")
        if payload.get("email") and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(payload["email"])):
            errors.append("email")
        if payload.get("phone") and not re.match(r"^\+?\d[\d\s().-]{6,}$", str(payload["phone"])):
            errors.append("phone")
        return {"valid": not errors, "errors": errors}
