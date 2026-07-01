from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionContext:
    """Shared context across workflow execution steps."""

    workflow_execution_id: int
    workflow_id: int
    application_id: int | None = None
    job_id: int | None = None
    profile_id: int | None = None
    current_step: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def set_data(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def add_error(self, error: str) -> None:
        self.errors.append(error)
