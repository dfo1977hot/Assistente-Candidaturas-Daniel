from __future__ import annotations


def validate_application(*, status: str) -> dict[str, object]:
    """Valida o resultado de uma automação."""
    return {"valid": status == "success"}
