from __future__ import annotations


def compare_versions(original: str, generated: str) -> dict[str, object]:
    """Compara duas versões de conteúdo para a interface."""
    return {
        "original": original,
        "generated": generated,
        "differences": [
            {"type": "updated", "original": original[:40], "generated": generated[:40]}
        ],
    }
