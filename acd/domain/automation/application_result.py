from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ApplicationResult:
    """Resultado estruturado de uma tentativa de candidatura."""

    status: str = "pending"
    message: str = ""
    screenshot_path: str = ""
    error: str = ""
