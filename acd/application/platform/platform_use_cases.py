"""Platform use cases orchestration."""

from typing import Any

from sqlalchemy.orm import Session

from acd.application.platform.services import (
    AuditService,
    BackupService,
    ConfigurationService,
    HealthService,
    MetricsService,
    RestoreService,
)
from acd.infrastructure.platform import StructuredLogger


class PlatformUseCases:
    """Orchestration for platform operations."""

    def __init__(self, session: Session, database_path: str = None) -> None:
        """Initialize use cases.

        Args:
            session: Database session
            database_path: Path to database file
        """
        self.session = session
        self.logger = StructuredLogger(__name__)

        # Initialize services
        self.health_service = HealthService(session)
        self.backup_service = BackupService(session, database_path)
        self.restore_service = RestoreService(session, database_path)
        self.configuration_service = ConfigurationService(session)
        self.metrics_service = MetricsService(session)
        self.audit_service = AuditService(session)

    # Health operations
    def get_system_health(self) -> dict[str, Any]:
        """Get system health status.

        Returns:
            System health
        """
        return self.health_service.get_overall_health()

    def run_health_check(self, check_name: str | None = None) -> dict[str, Any]:
        """Run health check.

        Args:
            check_name: Specific check or all if None

        Returns:
            Health check results
        """
        if check_name:
            result = self.health_service.run_specific_check(check_name)
            return {"check": check_name, "result": result} if result else {}

        return self.health_service.run_all_checks()

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
            Health history
        """
        return self.health_service.get_health_history(check_type, limit)

    # Backup operations
    def create_backup(
        self,
        backup_dir: str = "./backups",
        include_configs: bool = True,
        include_logs: bool = True,
    ) -> dict[str, Any]:
        """Create system backup.

        Args:
            backup_dir: Backup directory
            include_configs: Include configurations
            include_logs: Include logs

        Returns:
            Backup information
        """
        with self.logger.operation("create_backup"):
            result = self.backup_service.create_manual_backup(
                backup_dir,
                include_configs,
                include_logs,
            )

            # Log operation
            self.audit_service.log_critical_operation(
                "CREATE_BACKUP",
                "platform",
                details={"backup_id": result["backup_id"]},
            )

            return result

    def list_backups(self, status: str | None = None) -> list[dict[str, Any]]:
        """List system backups.

        Args:
            status: Filter by status

        Returns:
            List of backups
        """
        return self.backup_service.list_backups(status)

    def get_backup_info(self, backup_id: int) -> dict[str, Any] | None:
        """Get backup information.

        Args:
            backup_id: Backup ID

        Returns:
            Backup information
        """
        return self.backup_service.get_backup_info(backup_id)

    # Restore operations
    def restore_from_backup(
        self,
        backup_id: int,
        verify: bool = True,
    ) -> dict[str, Any]:
        """Restore from backup.

        Args:
            backup_id: Backup ID
            verify: Verify before restore

        Returns:
            Restore information
        """
        with self.logger.operation("restore_from_backup"):
            result = self.restore_service.restore_from_backup(backup_id, verify)

            # Log operation
            self.audit_service.log_critical_operation(
                "RESTORE_BACKUP",
                "platform",
                details={"backup_id": backup_id},
            )

            return result

    def list_restore_points(self) -> list[dict[str, Any]]:
        """List available restore points.

        Returns:
            Restore points
        """
        return self.restore_service.list_restore_points()

    # Configuration operations
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Configuration value
        """
        return self.configuration_service.get_config(key, default)

    def set_config(
        self,
        key: str,
        value: Any,
        config_type: str = "string",
        category: str = "system",
    ) -> dict[str, Any]:
        """Set configuration.

        Args:
            key: Configuration key
            value: Configuration value
            config_type: Configuration type
            category: Configuration category

        Returns:
            Configuration information
        """
        with self.logger.operation("set_config"):
            result = self.configuration_service.set_config(
                key,
                value,
                config_type,
                category,
            )

            # Log operation
            self.audit_service.log_critical_operation(
                "SET_CONFIG",
                "platform",
                details={"key": key},
            )

            return result

    def get_configuration_section(self, category: str) -> dict[str, Any]:
        """Get configuration section.

        Args:
            category: Configuration category

        Returns:
            Configurations in section
        """
        return self.configuration_service.get_section(category)

    def export_configuration(self) -> dict[str, Any]:
        """Export all configurations.

        Returns:
            All configurations
        """
        return self.configuration_service.export_config()

    # Metrics operations
    def collect_metrics(self) -> dict[str, Any]:
        """Collect system metrics.

        Returns:
            Collected metrics
        """
        return self.metrics_service.collect_system_metrics()

    def get_metrics(
        self,
        metric_name: str | None = None,
        category: str | None = None,
        hours_back: int = 1,
    ) -> list[dict[str, Any]]:
        """Get metrics.

        Args:
            metric_name: Metric name filter
            category: Category filter
            hours_back: Hours to look back

        Returns:
            Metrics
        """
        return self.metrics_service.get_metrics(metric_name, category, hours_back)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary.

        Returns:
            Summary
        """
        return self.metrics_service.get_system_summary()

    def get_performance_report(self, hours: int = 24) -> dict[str, Any]:
        """Get performance report.

        Args:
            hours: Hours to analyze

        Returns:
            Performance report
        """
        return self.metrics_service.get_performance_report(hours)

    # Audit operations
    def get_audit_trail(
        self,
        module: str | None = None,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """Get audit trail.

        Args:
            module: Module filter
            days: Days to look back

        Returns:
            Audit trail
        """
        return self.audit_service.get_audit_trail(module, None, days)

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
        return self.audit_service.get_user_activity(user_id, days)

    def get_failed_operations(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get failed operations.

        Args:
            hours: Hours to look back

        Returns:
            Failed operations
        """
        return self.audit_service.get_failed_operations(hours)

    def generate_compliance_report(self, days: int = 30) -> dict[str, Any]:
        """Generate compliance report.

        Args:
            days: Days to analyze

        Returns:
            Compliance report
        """
        return self.audit_service.generate_compliance_report(days)

    # System diagnostics
    def get_system_overview(self) -> dict[str, Any]:
        """Get complete system overview.

        Returns:
            System overview
        """
        with self.logger.operation("get_system_overview"):
            return {
                "health": self.health_service.get_overall_health(),
                "metrics": self.metrics_service.get_system_summary(),
                "backups": self.backup_service.list_backups(),
                "recent_errors": self.audit_service.get_failed_operations(hours=24),
            }
