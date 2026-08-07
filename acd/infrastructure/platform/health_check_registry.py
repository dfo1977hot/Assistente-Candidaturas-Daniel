"""Health check registry for extensible system diagnostics."""

from abc import ABC, abstractmethod
import time
from typing import Any

from acd.domain.platform.health_report import HealthCheckType, HealthStatus


class HealthCheck(ABC):
    """Abstract base for health checks."""

    @abstractmethod
    def check(self) -> dict[str, Any]:
        """Execute health check.

        Returns:
            Health check result with status, message, details
        """
        raise NotImplementedError

    @abstractmethod
    def get_name(self) -> str:
        """Get check name.

        Returns:
            Check name
        """
        raise NotImplementedError


class DatabaseHealthCheck(HealthCheck):
    """Database connectivity health check."""

    def __init__(self, session) -> None:
        """Initialize with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def get_name(self) -> str:
        """Get check name."""
        return HealthCheckType.DATABASE.value

    def check(self) -> dict[str, Any]:
        """Check database connectivity."""
        start_time = time.time()
        try:
            # Simple connectivity test
            self.session.execute("SELECT 1")
            duration_ms = (time.time() - start_time) * 1000

            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "Database is healthy",
                "details": {
                    "connection_time_ms": duration_ms,
                    "rows_affected": 1,
                },
                "response_time_ms": duration_ms,
            }
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Database check failed: {str(exc)}",
                "error_message": str(exc),
                "response_time_ms": duration_ms,
            }


class FilesystemHealthCheck(HealthCheck):
    """Filesystem access health check."""

    def __init__(self, paths: list[str] | None = None) -> None:
        """Initialize with paths to check.

        Args:
            paths: List of paths to verify
        """
        self.paths = paths or ["/"]

    def get_name(self) -> str:
        """Get check name."""
        return HealthCheckType.FILESYSTEM.value

    def check(self) -> dict[str, Any]:
        """Check filesystem health."""
        start_time = time.time()
        try:
            import os

            all_accessible = True
            inaccessible_paths = []

            for path in self.paths:
                if not os.path.exists(path):
                    all_accessible = False
                    inaccessible_paths.append(path)

            duration_ms = (time.time() - start_time) * 1000

            if all_accessible:
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "message": "Filesystem is healthy",
                    "details": {
                        "paths_checked": len(self.paths),
                        "all_accessible": True,
                    },
                    "response_time_ms": duration_ms,
                }
            else:
                return {
                    "status": HealthStatus.DEGRADED.value,
                    "message": f"Some paths are inaccessible: {inaccessible_paths}",
                    "details": {
                        "paths_checked": len(self.paths),
                        "inaccessible_paths": inaccessible_paths,
                    },
                    "response_time_ms": duration_ms,
                }
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Filesystem check failed: {str(exc)}",
                "error_message": str(exc),
                "response_time_ms": duration_ms,
            }


class MemoryHealthCheck(HealthCheck):
    """Memory usage health check."""

    def __init__(self, threshold_percent: float = 85.0) -> None:
        """Initialize with memory threshold.

        Args:
            threshold_percent: Memory usage threshold
        """
        self.threshold_percent = threshold_percent

    def get_name(self) -> str:
        """Get check name."""
        return HealthCheckType.MEMORY.value

    def check(self) -> dict[str, Any]:
        """Check memory health."""
        start_time = time.time()
        try:
            import psutil

            memory = psutil.virtual_memory()
            duration_ms = (time.time() - start_time) * 1000

            if memory.percent > self.threshold_percent:
                return {
                    "status": HealthStatus.DEGRADED.value,
                    "message": f"Memory usage is high: {memory.percent:.1f}%",
                    "details": {
                        "memory_percent": memory.percent,
                        "memory_available_mb": memory.available / (1024 * 1024),
                        "memory_total_mb": memory.total / (1024 * 1024),
                    },
                    "response_time_ms": duration_ms,
                }
            else:
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "message": f"Memory usage is normal: {memory.percent:.1f}%",
                    "details": {
                        "memory_percent": memory.percent,
                    },
                    "response_time_ms": duration_ms,
                }
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Memory check failed: {str(exc)}",
                "error_message": str(exc),
                "response_time_ms": duration_ms,
            }


class HealthCheckRegistry:
    """Registry for extensible health checks."""

    def __init__(self) -> None:
        """Initialize registry."""
        self.checks: dict[str, HealthCheck] = {}

    def register(self, health_check: HealthCheck) -> None:
        """Register a health check.

        Args:
            health_check: Health check to register
        """
        name = health_check.get_name()
        self.checks[name] = health_check

    def unregister(self, check_name: str) -> None:
        """Unregister a health check.

        Args:
            check_name: Name of check to unregister
        """
        if check_name in self.checks:
            del self.checks[check_name]

    def run_all(self) -> dict[str, dict[str, Any]]:
        """Run all registered health checks.

        Returns:
            Results from all checks
        """
        results = {}
        for check_name, check in self.checks.items():
            try:
                results[check_name] = check.check()
            except Exception as exc:
                results[check_name] = {
                    "status": HealthStatus.UNHEALTHY.value,
                    "message": f"Check failed: {str(exc)}",
                    "error_message": str(exc),
                }
        return results

    def run_check(self, check_name: str) -> dict[str, Any] | None:
        """Run a specific health check.

        Args:
            check_name: Name of check to run

        Returns:
            Check result or None if not found
        """
        if check_name not in self.checks:
            return None

        try:
            return self.checks[check_name].check()
        except Exception as exc:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Check failed: {str(exc)}",
                "error_message": str(exc),
            }

    def get_overall_status(self) -> str:
        """Get overall system health status.

        Returns:
            Overall status (HEALTHY, DEGRADED, UNHEALTHY)
        """
        results = self.run_all()

        if not results:
            return HealthStatus.UNKNOWN.value

        # Check for unhealthy
        if any(r.get("status") == HealthStatus.UNHEALTHY.value for r in results.values()):
            return HealthStatus.UNHEALTHY.value

        # Check for degraded
        if any(r.get("status") == HealthStatus.DEGRADED.value for r in results.values()):
            return HealthStatus.DEGRADED.value

        return HealthStatus.HEALTHY.value

    def get_list(self) -> list[str]:
        """Get list of registered checks.

        Returns:
            Check names
        """
        return list(self.checks.keys())


# Global registry instance
_registry: HealthCheckRegistry | None = None


def get_registry() -> HealthCheckRegistry:
    """Get global registry instance.

    Returns:
        Health check registry
    """
    global _registry
    if _registry is None:
        _registry = HealthCheckRegistry()
    return _registry
