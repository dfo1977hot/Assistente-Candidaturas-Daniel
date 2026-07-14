"""Application context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ApplicationContext:
    """Global application context."""

    settings: Any | None = None

    container: Any | None = None

    environment: str = "development"

    current_user: str | None = None

    current_project: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)