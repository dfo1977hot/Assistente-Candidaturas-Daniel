"""System log entity for structured logging."""

from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, DateTime

from acd.models.base import Base


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SystemLog(Base):
    """Structured system log entry."""

    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str]  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    module: Mapped[str] = mapped_column(index=True)
    operation: Mapped[str] = mapped_column(index=True)
    message: Mapped[str]
    duration_ms: Mapped[float] = mapped_column(default=0.0)
    result: Mapped[str] = mapped_column(default="success")  # success, failure, partial
    user_id: Mapped[int | None] = mapped_column(nullable=True)
    status_code: Mapped[int | None] = mapped_column(nullable=True)
    error_type: Mapped[str | None] = mapped_column(nullable=True)
    stack_trace: Mapped[str | None] = mapped_column(nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(nullable=True, index=True)
    request_id: Mapped[str | None] = mapped_column(nullable=True, index=True)
    context: Mapped[dict] = mapped_column(JSON, default={})
    extra_data: Mapped[dict] = mapped_column(JSON, default={})
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
    )

    def is_error(self) -> bool:
        """Check if log is an error."""
        return self.level in [LogLevel.ERROR.value, LogLevel.CRITICAL.value]

    def is_warning(self) -> bool:
        """Check if log is a warning."""
        return self.level == LogLevel.WARNING.value

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "level": self.level,
            "module": self.module,
            "operation": self.operation,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "result": self.result,
            "error_type": self.error_type,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
        }
