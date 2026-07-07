"""Service for metrics collection and analysis."""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from acd.infrastructure.platform import (
    StructuredLogger,
    get_collector,
)
from acd.infrastructure.repositories.platform import PlatformRepository


class MetricsService:
    """Service for metrics management."""

    def __init__(self, session: Session) -> None:
        """Initialize service.

        Args:
            session: Database session
        """
        self.session = session
        self.repository = PlatformRepository(session)
        self.logger = StructuredLogger(__name__)
        self.collector = get_collector()

    def collect_system_metrics(self) -> dict[str, Any]:
        """Collect current system metrics.

        Returns:
            System metrics
        """
        with self.logger.operation("collect_system_metrics"):
            metrics = self.collector.collect_system_metrics()

            # Record in database
            self.repository.record_metric(
                "memory_usage",
                metrics["memory_mb"],
                unit="MB",
                category="resource",
            )
            self.repository.record_metric(
                "cpu_usage",
                metrics["cpu_percent"],
                unit="%",
                category="resource",
            )
            self.repository.record_metric(
                "disk_usage",
                metrics["disk_usage_percent"],
                unit="%",
                category="resource",
            )

            return metrics

    def record_metric(
        self,
        metric_name: str,
        metric_value: float,
        unit: str = "",
        module: str = "system",
        category: str = "performance",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record a metric.

        Args:
            metric_name: Metric name
            metric_value: Metric value
            unit: Unit of measurement
            module: Module name
            category: Metric category
            tags: Tags for the metric

        Returns:
            Recorded metric
        """
        with self.logger.operation("record_metric"):
            metric = self.repository.record_metric(
                metric_name,
                metric_value,
                unit=unit,
                module=module,
                category=category,
                tags=tags or [],
            )

            return {
                "metric_name": metric.metric_name,
                "value": metric.metric_value,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat() if metric.timestamp else None,
            }

    def get_metrics(
        self,
        metric_name: str | None = None,
        category: str | None = None,
        hours_back: int = 1,
    ) -> list[dict[str, Any]]:
        """Get metrics.

        Args:
            metric_name: Filter by metric name
            category: Filter by category
            hours_back: Hours to look back

        Returns:
            Metrics
        """
        metrics = self.repository.get_metrics(
            metric_name=metric_name,
            category=category,
            hours_back=hours_back,
        )

        return [
            {
                "metric_name": m.metric_name,
                "value": m.metric_value,
                "unit": m.unit,
                "module": m.module,
                "category": m.category,
                "status": m.status,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in metrics
        ]

    def get_metric_statistics(
        self,
        metric_name: str,
        minutes: int = 60,
    ) -> dict[str, Any] | None:
        """Get statistics for a metric.

        Args:
            metric_name: Metric name
            minutes: Time window in minutes

        Returns:
            Metric statistics
        """
        stats = self.collector.get_metric_statistics(metric_name, minutes)
        return stats

    def get_system_summary(self) -> dict[str, Any]:
        """Get system metrics summary.

        Returns:
            System summary
        """
        with self.logger.operation("get_system_summary"):
            # Collect current metrics
            current = self.collect_system_metrics()

            # Get averages from last hour
            memory_stats = self.get_metric_statistics("memory_usage", 60)
            cpu_stats = self.get_metric_statistics("cpu_usage", 60)
            disk_stats = self.get_metric_statistics("disk_usage", 60)

            return {
                "timestamp": datetime.now().isoformat(),
                "current": {
                    "memory_mb": current["memory_mb"],
                    "cpu_percent": current["cpu_percent"],
                    "disk_usage_percent": current["disk_usage_percent"],
                    "uptime_seconds": current["uptime_seconds"],
                },
                "averages": {
                    "memory_mb": memory_stats.get("avg") if memory_stats else None,
                    "cpu_percent": cpu_stats.get("avg") if cpu_stats else None,
                    "disk_usage_percent": disk_stats.get("avg") if disk_stats else None,
                },
                "extremes": {
                    "memory_max": memory_stats.get("max") if memory_stats else None,
                    "cpu_max": cpu_stats.get("max") if cpu_stats else None,
                    "disk_max": disk_stats.get("max") if disk_stats else None,
                },
            }

    def get_performance_report(
        self,
        hours: int = 24,
    ) -> dict[str, Any]:
        """Get performance report.

        Args:
            hours: Hours to analyze

        Returns:
            Performance report
        """
        with self.logger.operation("get_performance_report"):
            # Get all metrics from last N hours
            memory_metrics = self.get_metrics("memory_usage", hours_back=hours)
            cpu_metrics = self.get_metrics("cpu_usage", hours_back=hours)

            # Calculate statistics
            def calc_stats(metrics):
                if not metrics:
                    return None
                values = [m["value"] for m in metrics]
                return {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values),
                }

            return {
                "report_timestamp": datetime.now().isoformat(),
                "period_hours": hours,
                "memory": calc_stats(memory_metrics),
                "cpu": calc_stats(cpu_metrics),
            }

    def cleanup_old_metrics(self, older_than_hours: int = 24) -> int:
        """Clean up old metrics.

        Args:
            older_than_hours: Hours threshold

        Returns:
            Number of metrics cleaned
        """
        with self.logger.operation("cleanup_old_metrics"):
            return self.collector.clear_old_metrics(older_than_hours)
