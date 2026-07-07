"""System metrics entity for performance monitoring."""

from datetime import datetime

from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from acd.models.base import Base


class SystemMetrics(Base):
    """Performance and usage metrics."""

    __tablename__ = "system_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_name: Mapped[str] = mapped_column(index=True)
    metric_value: Mapped[float]
    unit: Mapped[str] = mapped_column(default="")  # ms, MB, %, count, etc
    module: Mapped[str] = mapped_column(index=True)
    category: Mapped[str] = mapped_column(index=True)  # performance, resource, business
    tags: Mapped[list[str]] = mapped_column(JSON, default=[])
    min_value: Mapped[float | None] = mapped_column(nullable=True)
    max_value: Mapped[float | None] = mapped_column(nullable=True)
    avg_value: Mapped[float | None] = mapped_column(nullable=True)
    threshold_warning: Mapped[float | None] = mapped_column(nullable=True)
    threshold_critical: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(default="normal")  # normal, warning, critical
    metric_metadata: Mapped[dict] = mapped_column(JSON, default={})
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
    )

    def is_warning(self) -> bool:
        """Check if metric is in warning state."""
        return self.status == "warning"

    def is_critical(self) -> bool:
        """Check if metric is critical."""
        return self.status == "critical"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "unit": self.unit,
            "module": self.module,
            "category": self.category,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
        }
