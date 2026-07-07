from __future__ import annotations


def explain_changes(*, explanation: str) -> dict[str, object]:
    """Formata uma explicação para a interface."""
    return {
        "explanation": explanation,
        "items": [item.strip() for item in explanation.split(".") if item.strip()],
    }
