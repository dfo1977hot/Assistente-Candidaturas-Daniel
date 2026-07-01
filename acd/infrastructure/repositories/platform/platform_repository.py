"""Repository for platform entities."""

from typing import Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from acd.domain.platform.health_report import HealthReport
from acd.domain.platform.system_status import SystemStatus
from acd.domain.platform.system_log import SystemLog
from acd.domain.platform.system_metrics import SystemMetrics
from acd.domain.platform.backup import Backup
from acd.domain.platform.configuration import Configuration


class PlatformRepository:
    """Repository for platform domain entities."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    # Health Report operations
    def create_health_report(
        self,
        check_type: str,
        status: str,
        message: str,
        details: dict[str, Any] | None = None,
        error_message: str | None = None,
        response_time_ms: float = 0.0,
    ) -> HealthReport:
        """Create health report.

        Args:
            check_type: Type of check
            status: Health status
            message: Status message
            details: Additional details
            error_message: Error message if applicable
            response_time_ms: Response time

        Returns:
            Created health report
        """
        report = HealthReport(
            check_type=check_type,
            status=status,
            message=message,
            details=details or {},
            error_message=error_message,
            response_time_ms=response_time_ms,
        )
        self.session.add(report)
        self.session.commit()
        return report

    def list_health_reports(
        self,
        limit: int = 100,
        check_type: str | None = None,
    ) -> list[HealthReport]:
        """List health reports.

        Args:
            limit: Result limit
            check_type: Filter by check type

        Returns:
            Health reports
        """
        query = self.session.query(HealthReport)
        if check_type:
            query = query.filter(HealthReport.check_type == check_type)

        return query.order_by(desc(HealthReport.timestamp)).limit(limit).all()

    # System Status operations
    def get_or_create_status(self) -> SystemStatus:
        """Get or create system status.

        Returns:
            System status entity
        """
        status = self.session.query(SystemStatus).first()
        if not status:
            status = SystemStatus(overall_status="unknown")
            self.session.add(status)
            self.session.commit()
        return status

    def update_status(
        self,
        overall_status: str,
        **kwargs
    ) -> SystemStatus:
        """Update system status.

        Args:
            overall_status: New overall status
            **kwargs: Additional fields to update

        Returns:
            Updated status
        """
        status = self.get_or_create_status()
        status.overall_status = overall_status
        status.timestamp = datetime.now()

        for key, value in kwargs.items():
            if hasattr(status, key):
                setattr(status, key, value)

        self.session.commit()
        return status

    # System Log operations
    def create_log(
        self,
        level: str,
        module: str,
        operation: str,
        message: str,
        **kwargs
    ) -> SystemLog:
        """Create system log entry.

        Args:
            level: Log level
            module: Module name
            operation: Operation name
            message: Log message
            **kwargs: Additional fields

        Returns:
            Created log entry
        """
        log = SystemLog(
            level=level,
            module=module,
            operation=operation,
            message=message,
            **kwargs
        )
        self.session.add(log)
        self.session.commit()
        return log

    def list_logs(
        self,
        level: str | None = None,
        module: str | None = None,
        hours_back: int = 24,
        limit: int = 1000,
    ) -> list[SystemLog]:
        """List system logs.

        Args:
            level: Filter by level
            module: Filter by module
            hours_back: Hours to look back
            limit: Result limit

        Returns:
            System logs
        """
        cutoff = datetime.now() - timedelta(hours=hours_back)
        query = self.session.query(SystemLog).filter(SystemLog.timestamp >= cutoff)

        if level:
            query = query.filter(SystemLog.level == level)
        if module:
            query = query.filter(SystemLog.module == module)

        return query.order_by(desc(SystemLog.timestamp)).limit(limit).all()

    def get_error_count(self, hours: int = 24) -> int:
        """Get error count in time period.

        Args:
            hours: Hours to count

        Returns:
            Error count
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        return self.session.query(SystemLog).filter(
            and_(
                SystemLog.timestamp >= cutoff,
                SystemLog.level.in_(["ERROR", "CRITICAL"])
            )
        ).count()

    # System Metrics operations
    def record_metric(
        self,
        metric_name: str,
        metric_value: float,
        unit: str = "",
        module: str = "system",
        category: str = "performance",
        **kwargs
    ) -> SystemMetrics:
        """Record system metric.

        Args:
            metric_name: Metric name
            metric_value: Metric value
            unit: Unit of measurement
            module: Module name
            category: Metric category
            **kwargs: Additional fields

        Returns:
            Recorded metric
        """
        metric = SystemMetrics(
            metric_name=metric_name,
            metric_value=metric_value,
            unit=unit,
            module=module,
            category=category,
            **kwargs
        )
        self.session.add(metric)
        self.session.commit()
        return metric

    def get_metrics(
        self,
        metric_name: str | None = None,
        category: str | None = None,
        hours_back: int = 1,
        limit: int = 1000,
    ) -> list[SystemMetrics]:
        """Get system metrics.

        Args:
            metric_name: Filter by metric name
            category: Filter by category
            hours_back: Hours to look back
            limit: Result limit

        Returns:
            System metrics
        """
        cutoff = datetime.now() - timedelta(hours=hours_back)
        query = self.session.query(SystemMetrics).filter(SystemMetrics.timestamp >= cutoff)

        if metric_name:
            query = query.filter(SystemMetrics.metric_name == metric_name)
        if category:
            query = query.filter(SystemMetrics.category == category)

        return query.order_by(desc(SystemMetrics.timestamp)).limit(limit).all()

    # Backup operations
    def create_backup(
        self,
        backup_type: str,
        name: str,
        file_path: str,
        **kwargs
    ) -> Backup:
        """Create backup record.

        Args:
            backup_type: Type of backup
            name: Backup name
            file_path: Path to backup file
            **kwargs: Additional fields

        Returns:
            Created backup
        """
        backup = Backup(
            backup_type=backup_type,
            status="pending",
            name=name,
            file_path=file_path,
            **kwargs
        )
        self.session.add(backup)
        self.session.commit()
        return backup

    def update_backup_status(
        self,
        backup_id: int,
        status: str,
        **kwargs
    ) -> Backup | None:
        """Update backup status.

        Args:
            backup_id: Backup ID
            status: New status
            **kwargs: Additional fields

        Returns:
            Updated backup or None
        """
        backup = self.session.query(Backup).filter(Backup.id == backup_id).first()
        if backup:
            backup.status = status
            if status == "completed":
                backup.completed_at = datetime.now()
            elif status == "restored":
                backup.restored_at = datetime.now()

            for key, value in kwargs.items():
                if hasattr(backup, key):
                    setattr(backup, key, value)

            self.session.commit()
        return backup

    def list_backups(
        self,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Backup]:
        """List backups.

        Args:
            status: Filter by status
            limit: Result limit

        Returns:
            Backups
        """
        query = self.session.query(Backup)
        if status:
            query = query.filter(Backup.status == status)

        return query.order_by(desc(Backup.created_at)).limit(limit).all()

    # Configuration operations
    def set_config(
        self,
        key: str,
        value: str,
        config_type: str = "string",
        category: str = "system",
        **kwargs
    ) -> Configuration:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
            config_type: Type of configuration
            category: Configuration category
            **kwargs: Additional fields

        Returns:
            Configuration entity
        """
        config = self.session.query(Configuration).filter(Configuration.key == key).first()
        if not config:
            config = Configuration(
                key=key,
                value=value,
                config_type=config_type,
                category=category,
                **kwargs
            )
            self.session.add(config)
        else:
            config.value = value
            for k, v in kwargs.items():
                if hasattr(config, k):
                    setattr(config, k, v)

        self.session.commit()
        return config

    def get_config(self, key: str) -> Configuration | None:
        """Get configuration.

        Args:
            key: Configuration key

        Returns:
            Configuration or None
        """
        return self.session.query(Configuration).filter(Configuration.key == key).first()

    def get_all_configs(self, category: str | None = None) -> list[Configuration]:
        """Get all configurations.

        Args:
            category: Filter by category

        Returns:
            All configurations
        """
        query = self.session.query(Configuration)
        if category:
            query = query.filter(Configuration.category == category)

        return query.all()
