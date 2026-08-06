"""Kernel event contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class EventType(StrEnum):
    """Supported event types."""

    APPLICATION = "application"
    COMPANY = "company"
    JOB = "job"
    LEARNING = "learning"
    PLANNER = "planner"
    PIPELINE = "pipeline"
    WORKFLOW = "workflow"
    SYSTEM = "system"


@dataclass(slots=True)
class DomainEvent:
    """Base domain event."""

    event_type: EventType
    name: str
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# Backward-compatible alias
Event = DomainEvent


class EventHandler(ABC):
    """Base event handler."""

    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """Handle an event."""
