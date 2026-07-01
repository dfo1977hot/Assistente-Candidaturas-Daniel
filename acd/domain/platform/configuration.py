"""Configuration entity for system settings."""

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, DateTime

from acd.models.base import Base


class Configuration(Base):
    """System configuration settings."""

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(unique=True, index=True)
    value: Mapped[str]
    config_type: Mapped[str] = mapped_column(index=True)  # string, integer, boolean, json
    category: Mapped[str] = mapped_column(index=True)  # system, ui, ai, connectors, etc
    description: Mapped[str] = mapped_column(default="")
    default_value: Mapped[str | None] = mapped_column(nullable=True)
    is_secret: Mapped[bool] = mapped_column(default=False)  # Sensitive config
    is_required: Mapped[bool] = mapped_column(default=False)
    validation_rules: Mapped[dict] = mapped_column(JSON, default={})  # min, max, pattern, etc
    environment_override: Mapped[str | None] = mapped_column(nullable=True)  # Env var name
    config_metadata: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
    )

    def get_typed_value(self):
        """Get value with correct type."""
        if self.config_type == "boolean":
            return self.value.lower() in ("true", "1", "yes")
        elif self.config_type == "integer":
            return int(self.value)
        elif self.config_type == "json":
            import json
            return json.loads(self.value)
        return self.value

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value if not self.is_secret else "***",
            "config_type": self.config_type,
            "category": self.category,
            "description": self.description,
            "updated_at": self.updated_at.isoformat(),
        }
