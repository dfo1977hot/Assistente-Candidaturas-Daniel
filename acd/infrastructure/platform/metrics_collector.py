"""Metrics collector for system performance monitoring."""

from collections import defaultdict
from datetime import datetime, timedelta
import time
from typing import Any

import psutil

from acd.domain.platform.system_metrics import SystemMetrics


class MetricsCollector:
    """Collects and manages system metrics."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.metrics: dict[str, list[SystemMetrics]] = defaultdict(list)
        self.start_time = time.time()

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB.

        Returns:
            Memory usage in MB
        """
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage.

        Returns:
            CPU usage percentage
        """
        return psutil.cpu_percent(interval=0.1)

    def get_disk_usage(self, path: str = "/") -> float:
        """Get disk usage percentage.

        Args:
            path: Path to check

        Returns:
            Disk usage percentage
        """
        try:
            disk = psutil.disk_usage(path)
            return (disk.used / disk.total) * 100
        except Exception:
            return 0.0

    def get_uptime(self) -> int:
        """Get uptime in seconds.

        Returns:
            Uptime in seconds
        """
        return int(time.time() - self.start_time)

    def get_system_load(self) -> tuple[float, float, float]:
        """Get system load averages.

        Returns:
            Tuple of (1min, 5min, 15min) load averages
        """
        return psutil.getloadavg()

    def record_metric(
        self,
        metric_name: str,
        metric_value: float,
        unit: str = "",
        module: str = "system",
        category: str = "performance",
        tags: list[str] | None = None,
        threshold_warning: float | None = None,
        threshold_critical: float | None = None,
    ) -> dict[str, Any]:
        """Record a metric.

        Args:
            metric_name: Name of metric
            metric_value: Metric value
            unit: Unit of measurement
            module: Module name
            category: Metric category
            tags: Tags for the metric
            threshold_warning: Warning threshold
            threshold_critical: Critical threshold

        Returns:
            Metric data
        """
        # Determine status based on thresholds
        status = "normal"
        if threshold_critical and metric_value >= threshold_critical:
            status = "critical"
        elif threshold_warning and metric_value >= threshold_warning:
            status = "warning"

        metric_data = {
            "metric_name": metric_name,
            "metric_value": metric_value,
            "unit": unit,
            "module": module,
            "category": category,
            "tags": tags or [],
            "threshold_warning": threshold_warning,
            "threshold_critical": threshold_critical,
            "status": status,
            "timestamp": datetime.now(),
        }

        self.metrics[metric_name].append(metric_data)

        # Keep only last 1000 samples per metric
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]

        return metric_data

    def get_metric_statistics(
        self,
        metric_name: str,
        minutes: int = 60,
    ) -> dict[str, Any] | None:
        """Get statistics for a metric.

        Args:
            metric_name: Name of metric
            minutes: Time window in minutes

        Returns:
            Metric statistics or None if not found
        """
        if metric_name not in self.metrics:
            return None

        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.metrics[metric_name] if m["timestamp"] >= cutoff_time]

        if not recent_metrics:
            return None

        values = [m["metric_value"] for m in recent_metrics]

        return {
            "metric_name": metric_name,
            "samples": len(recent_metrics),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "time_window_minutes": minutes,
        }

    def collect_system_metrics(self) -> dict[str, Any]:
        """Collect all current system metrics.

        Returns:
            System metrics snapshot
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "memory_mb": self.get_memory_usage(),
            "cpu_percent": self.get_cpu_usage(),
            "disk_usage_percent": self.get_disk_usage(),
            "uptime_seconds": self.get_uptime(),
            "system_load": self.get_system_load(),
        }

        # Record metrics
        self.record_metric("memory_usage", metrics["memory_mb"], "MB", category="resource")
        self.record_metric("cpu_usage", metrics["cpu_percent"], "%", category="resource")
        self.record_metric("disk_usage", metrics["disk_usage_percent"], "%", category="resource")

        return metrics

    def get_all_metrics(self) -> dict[str, list[dict[str, Any]]]:
        """Get all recorded metrics.

        Returns:
            All metrics organized by name
        """
        return {
            metric_name: [
                {
                    "metric_name": m["metric_name"],
                    "metric_value": m["metric_value"],
                    "unit": m["unit"],
                    "status": m["status"],
                    "timestamp": m["timestamp"].isoformat(),
                }
                for m in metrics
            ]
            for metric_name, metrics in self.metrics.items()
        }

    def clear_old_metrics(self, older_than_hours: int = 24) -> int:
        """Clear metrics older than specified hours.

        Args:
            older_than_hours: Hours threshold

        Returns:
            Number of metrics cleared
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cleared = 0

        for metric_name in self.metrics:
            original_count = len(self.metrics[metric_name])
            self.metrics[metric_name] = [
                m for m in self.metrics[metric_name] if m["timestamp"] >= cutoff_time
            ]
            cleared += original_count - len(self.metrics[metric_name])

        return cleared


# Global collector instance
_collector: MetricsCollector | None = None


def get_collector() -> MetricsCollector:
    """Get global collector instance.

    Returns:
        Metrics collector
    """
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
