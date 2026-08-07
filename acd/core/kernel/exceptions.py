"""Kernel exceptions."""

from __future__ import annotations


class KernelError(Exception):
    """Base exception for the Kernel."""


class ServiceNotRegisteredError(KernelError):
    """Raised when a service has not been registered."""


class CircularDependencyError(KernelError):
    """Raised when a circular dependency is detected."""


class ServiceAlreadyRegisteredError(KernelError):
    """Raised when attempting to register a duplicated service."""