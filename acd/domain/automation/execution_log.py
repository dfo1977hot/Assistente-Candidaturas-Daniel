from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ExecutionLog:
    """Entry para o timeline de execução de automação."""

    event: str
    details: str
