"""Application bootstrap."""

from __future__ import annotations

from acd.core.kernel.application_context import ApplicationContext
from acd.core.kernel.dependency_container import DependencyContainer
from acd.core.kernel.lifecycle import LifecycleState


class Bootstrap:
    """Application bootstrap."""

    def __init__(self) -> None:
        self.context = ApplicationContext()

        self.container = DependencyContainer()

        self.state = LifecycleState.CREATED

    def initialize(self) -> None:
        """Initialize application."""

        self.state = LifecycleState.INITIALIZING

        self.context.container = self.container

        self.state = LifecycleState.READY