"""System status entity for platform health monitoring."""

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, DateTime

from acd.models.base import Base


class SystemStatus(Base):
    """Overall system status and metrics."""

    __tablename__ = "system_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    overall_status: Mapped[str]  # HEALTHY, DEGRADED, UNHEALTHY
    uptime_seconds: Mapped[int] = mapped_column(default=0)
    memory_usage_mb: Mapped[float] = mapped_column(default=0.0)
    cpu_usage_percent: Mapped[float] = mapped_column(default=0.0)
    active_workflows: Mapped[int] = mapped_column(default=0)
    active_automations: Mapped[int] = mapped_column(default=0)
    last_backup_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    errors_24h: Mapped[int] = mapped_column(default=0)
    warnings_24h: Mapped[int] = mapped_column(default=0)
    avg_response_time_ms: Mapped[float] = mapped_column(default=0.0)
    disk_usage_percent: Mapped[float] = mapped_column(default=0.0)
    database_size_mb: Mapped[float] = mapped_column(default=0.0)
    health_checks_status: Mapped[dict] = mapped_column(JSON, default={})
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )

    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.overall_status == "healthy"

    def is_degraded(self) -> bool:
        """Check if system is degraded."""
        return self.overall_status == "degraded"

    def is_unhealthy(self) -> bool:
        """Check if system is unhealthy."""
        return self.overall_status == "unhealthy"

    def get_health_score(self) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0

        # Deduct for errors and warnings
        score -= min(50, self.errors_24h * 2)
        score -= min(20, self.warnings_24h)

        # Deduct for high resource usage
        if self.memory_usage_mb > 2048:
            score -= 15
        if self.cpu_usage_percent > 80:
            score -= 15
        if self.disk_usage_percent > 80:
            score -= 20

        # Deduct for slow response time
        if self.avg_response_time_ms > 2000:
            score -= 10

        return max(0, min(100, score))

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "overall_status": self.overall_status,
            "uptime_seconds": self.uptime_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "active_workflows": self.active_workflows,
            "active_automations": self.active_automations,
            "errors_24h": self.errors_24h,
            "warnings_24h": self.warnings_24h,
            "avg_response_time_ms": self.avg_response_time_ms,
            "disk_usage_percent": self.disk_usage_percent,
            "database_size_mb": self.database_size_mb,
            "health_score": self.get_health_score(),
            "timestamp": self.timestamp.isoformat(),
        }
