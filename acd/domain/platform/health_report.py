"""Health report entity for system health checks."""

from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, DateTime

from acd.models.base import Base


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckType(str, Enum):
    """Types of health checks."""

    DATABASE = "database"
    FILESYSTEM = "filesystem"
    MEMORY = "memory"
    AI_SERVICE = "ai_service"
    CONNECTORS = "connectors"
    CONFIGURATION = "configuration"
    DIRECTORIES = "directories"
    PLAYWRIGHT = "playwright"


class HealthReport(Base):
    """Health check report for system diagnostics."""

    __tablename__ = "health_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_type: Mapped[str] = mapped_column(index=True)
    status: Mapped[str]  # HEALTHY, DEGRADED, UNHEALTHY
    message: Mapped[str]
    details: Mapped[dict] = mapped_column(JSON, default={})
    error_message: Mapped[str | None] = mapped_column(nullable=True)
    response_time_ms: Mapped[float] = mapped_column(default=0.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
    )
    last_checked: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def is_healthy(self) -> bool:
        """Check if report is healthy."""
        return self.status == HealthStatus.HEALTHY.value

    def is_degraded(self) -> bool:
        """Check if report is degraded."""
        return self.status == HealthStatus.DEGRADED.value

    def is_unhealthy(self) -> bool:
        """Check if report is unhealthy."""
        return self.status == HealthStatus.UNHEALTHY.value

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "check_type": self.check_type,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
