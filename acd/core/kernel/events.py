"""Kernel event contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
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
    SYSTEM = "system"


@dataclass(slots=True)
class Event:
    """Base event."""

    event_type: EventType

    name: str

    payload: dict[str, Any]

    timestamp: datetime = datetime.now(UTC)


class EventHandler(ABC):
    """Base event handler."""

    @abstractmethod
    def handle(
        self,
        event: Event,
    ) -> None:
        """Handle an event."""