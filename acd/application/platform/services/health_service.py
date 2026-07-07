"""Service for system health monitoring."""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from acd.domain.platform.health_report import HealthStatus
from acd.infrastructure.platform import (
    StructuredLogger,
    get_registry,
)
from acd.infrastructure.repositories.platform import PlatformRepository


class HealthService:
    """Service for health check management."""

    def __init__(self, session: Session) -> None:
        """Initialize service.

        Args:
            session: Database session
        """
        self.session = session
        self.repository = PlatformRepository(session)
        self.logger = StructuredLogger(__name__)

    def run_all_checks(self) -> dict[str, Any]:
        """Run all registered health checks.

        Returns:
            Results from all checks
        """
        self.logger.debug("run_all_checks", "Starting health checks")

        registry = get_registry()
        results = registry.run_all()

        # Save results
        for check_name, result in results.items():
            self.repository.create_health_report(
                check_type=check_name,
                status=result.get("status", HealthStatus.UNKNOWN.value),
                message=result.get("message", ""),
                details=result.get("details"),
                error_message=result.get("error_message"),
                response_time_ms=result.get("response_time_ms", 0),
            )

        return results

    def run_specific_check(self, check_name: str) -> dict[str, Any] | None:
        """Run specific health check.

        Args:
            check_name: Name of check

        Returns:
            Check result
        """
        self.logger.debug("run_specific_check", f"Running check: {check_name}")

        registry = get_registry()
        result = registry.run_check(check_name)

        if result:
            self.repository.create_health_report(
                check_type=check_name,
                status=result.get("status", HealthStatus.UNKNOWN.value),
                message=result.get("message", ""),
                details=result.get("details"),
                error_message=result.get("error_message"),
                response_time_ms=result.get("response_time_ms", 0),
            )

        return result

    def get_overall_health(self) -> dict[str, Any]:
        """Get overall system health.

        Returns:
            Overall health information
        """
        registry = get_registry()
        overall_status = registry.get_overall_status()

        with self.logger.operation("get_overall_health"):
            self.repository.get_or_create_status()
            status_data = {
                "overall_status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "checks": registry.run_all(),
            }

            # Update system status
            self.repository.update_status(overall_status)

            return status_data

    def get_health_history(
        self,
        check_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get health check history.

        Args:
            check_type: Filter by check type
            limit: Result limit

        Returns:
            Health reports
        """
        reports = self.repository.list_health_reports(limit=limit, check_type=check_type)
        return [
            {
                "id": r.id,
                "check_type": r.check_type,
                "status": r.status,
                "message": r.message,
                "response_time_ms": r.response_time_ms,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in reports
        ]
