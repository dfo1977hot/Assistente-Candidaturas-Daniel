"""Application bootstrap."""

from __future__ import annotations

from acd.core.kernel.application_context import ApplicationContext
from acd.core.kernel.dependency_container import DependencyContainer
from acd.core.kernel.kernel import Kernel
from acd.core.kernel.lifecycle import LifecycleState
from acd.services.planner import PlannerService


class Bootstrap:
    """Application bootstrap."""

    def __init__(self) -> None:
        self.kernel = Kernel()

        self.context = self.kernel.context
        self.container = self.kernel.container
        self.services = self.kernel.services

        self.state = LifecycleState.CREATED

        self.services.register(Kernel, self.kernel)
        self.services.register(ApplicationContext, self.context)
        self.services.register(DependencyContainer, self.container)

        planner_service = PlannerService()

        self.register_service(PlannerService, planner_service,)

    def initialize(self) -> None:
        """Initialize application."""

        self.state = LifecycleState.INITIALIZING

        self.context.container = self.container

        self.state = LifecycleState.READY

    def register_service(
        self,
        service_type: type,
        instance: object,
    ) -> None:
        """Register a service in the application registry."""

        self.services.register(service_type, instance)

    def resolve_service(
        self,
        service_type: type,
    ) -> object:
        """Resolve a service from the application registry."""

        return self.services.resolve(service_type)