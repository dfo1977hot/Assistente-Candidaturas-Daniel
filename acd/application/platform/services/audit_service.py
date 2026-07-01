"""Service for audit logging and compliance tracking."""

from typing import Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from acd.infrastructure.platform import StructuredLogger
from acd.infrastructure.repositories.platform import PlatformRepository
from acd.domain.platform.system_log import LogLevel


class AuditService:
    """Service for audit logging."""

    def __init__(self, session: Session) -> None:
        """Initialize service.

        Args:
            session: Database session
        """
        self.session = session
        self.repository = PlatformRepository(session)
        self.logger = StructuredLogger(__name__)

    def log_critical_operation(
        self,
        operation: str,
        module: str,
        user_id: str | None = None,
        details: dict[str, Any] | None = None,
        result: str = "success",
    ) -> dict[str, Any]:
        """Log critical operation.

        Args:
            operation: Operation name
            module: Module name
            user_id: User who performed operation
            details: Operation details
            result: Operation result

        Returns:
            Log entry
        """
        with self.logger.operation("log_critical_operation"):
            log_entry = self.repository.create_log(
                LogLevel.WARNING.value,
                module,
                operation,
                f"Critical operation: {operation}",
                user_id=user_id,
                result=result,
                metadata=details or {},
            )

            return {
                "id": log_entry.id,
                "operation": operation,
                "timestamp": log_entry.timestamp.isoformat() if log_entry.timestamp else None,
            }

    def get_audit_trail(
        self,
        module: str | None = None,
        operation: str | None = None,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """Get audit trail.

        Args:
            module: Filter by module
            operation: Filter by operation
            days: Days to look back

        Returns:
            Audit trail
        """
        logs = self.repository.list_logs(
            level=LogLevel.WARNING.value,
            module=module,
            hours_back=days * 24,
        )

        filtered = [l for l in logs if operation is None or l.operation == operation]

        return [
            {
                "id": l.id,
                "operation": l.operation,
                "module": l.module,
                "message": l.message,
                "result": l.result,
                "user_id": l.user_id,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "metadata": l.metadata,
            }
            for l in filtered
        ]

    def get_user_activity(
        self,
        user_id: str,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """Get user activity.

        Args:
            user_id: User ID
            days: Days to look back

        Returns:
            User activity
        """
        logs = self.repository.list_logs(hours_back=days * 24)
        user_logs = [l for l in logs if l.user_id == user_id]

        return [
            {
                "id": l.id,
                "operation": l.operation,
                "module": l.module,
                "level": l.level,
                "result": l.result,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in user_logs
        ]

    def get_failed_operations(
        self,
        hours: int = 24,
    ) -> list[dict[str, Any]]:
        """Get failed operations.

        Args:
            hours: Hours to look back

        Returns:
            Failed operations
        """
        logs = self.repository.list_logs(
            level=LogLevel.ERROR.value,
            hours_back=hours,
        )

        return [
            {
                "id": l.id,
                "operation": l.operation,
                "module": l.module,
                "message": l.message,
                "error_type": l.error_type,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in logs
        ]

    def generate_compliance_report(
        self,
        days: int = 30,
    ) -> dict[str, Any]:
        """Generate compliance report.

        Args:
            days: Days to analyze

        Returns:
            Compliance report
        """
        with self.logger.operation("generate_compliance_report"):
            logs = self.repository.list_logs(hours_back=days * 24)

            # Calculate statistics
            total_operations = len(logs)
            errors = len([l for l in logs if l.level == LogLevel.ERROR.value])
            warnings = len([l for l in logs if l.level == LogLevel.WARNING.value])

            # Group by module
            modules = {}
            for log in logs:
                if log.module not in modules:
                    modules[log.module] = {
                        "total": 0,
                        "errors": 0,
                        "warnings": 0,
                    }
                modules[log.module]["total"] += 1
                if log.level == LogLevel.ERROR.value:
                    modules[log.module]["errors"] += 1
                elif log.level == LogLevel.WARNING.value:
                    modules[log.module]["warnings"] += 1

            return {
                "report_timestamp": datetime.now().isoformat(),
                "period_days": days,
                "total_operations": total_operations,
                "total_errors": errors,
                "total_warnings": warnings,
                "error_rate": (errors / total_operations * 100) if total_operations > 0 else 0,
                "modules": modules,
            }

    def export_audit_log(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Export audit log for compliance.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Exported logs
        """
        # Get all logs in range
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        hours_back = int((end_date - start_date).total_seconds() / 3600)
        logs = self.repository.list_logs(hours_back=hours_back)

        return [
            {
                "id": l.id,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "level": l.level,
                "module": l.module,
                "operation": l.operation,
                "message": l.message,
                "user_id": l.user_id,
                "result": l.result,
                "error_type": l.error_type,
                "correlation_id": l.correlation_id,
            }
            for l in logs
        ]
