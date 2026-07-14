"""
ACD Kernel.

Central entry point for all kernel services.
"""

from __future__ import annotations

from acd.core.kernel.application_context import ApplicationContext
from acd.core.kernel.command_bus import CommandBus
from acd.core.kernel.dependency_container import DependencyContainer
from acd.core.kernel.event_bus import EventBus
from acd.core.kernel.query_bus import QueryBus
from acd.core.kernel.service_registry import ServiceRegistry


class Kernel:
    """Application Kernel."""

    def __init__(self) -> None:

        self.context = ApplicationContext()

        self.services = ServiceRegistry()

        self.container = DependencyContainer()

        self.events = EventBus()

        self.commands = CommandBus()

        self.queries = QueryBus()

    def clear(self) -> None:
        """Reset kernel state."""

        self.services.clear()

        self.container.clear()

        self.events.clear()

        self.commands.clear()

        self.queries.clear()