"""Service for configuration management."""

from typing import Any
from sqlalchemy.orm import Session

from acd.infrastructure.platform import (
    StructuredLogger,
    get_provider,
)
from acd.infrastructure.repositories.platform import PlatformRepository


class ConfigurationService:
    """Service for configuration management."""

    def __init__(self, session: Session) -> None:
        """Initialize service.

        Args:
            session: Database session
        """
        self.session = session
        self.repository = PlatformRepository(session)
        self.logger = StructuredLogger(__name__)

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Configuration value
        """
        with self.logger.operation("get_config"):
            # Try provider first
            provider = get_provider()
            value = provider.get(key)
            if value is not None:
                return value

            # Try repository
            config = self.repository.get_config(key)
            if config:
                return config.get_typed_value()

            return default

    def set_config(
        self,
        key: str,
        value: Any,
        config_type: str = "string",
        category: str = "system",
        description: str | None = None,
    ) -> dict[str, Any]:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
            config_type: Type of configuration
            category: Configuration category
            description: Configuration description

        Returns:
            Configuration information
        """
        with self.logger.operation("set_config"):
            config = self.repository.set_config(
                key,
                str(value),
                config_type=config_type,
                category=category,
                description=description,
            )

            # Update provider cache
            provider = get_provider()
            provider.set(key, value)

            return {
                "key": config.key,
                "value": config.get_typed_value(),
                "type": config.config_type,
                "category": config.category,
            }

    def get_section(self, category: str) -> dict[str, Any]:
        """Get all configurations in a category.

        Args:
            category: Configuration category

        Returns:
            Configurations in category
        """
        with self.logger.operation("get_section"):
            configs = self.repository.get_all_configs(category=category)
            return {
                c.key: c.get_typed_value() for c in configs
            }

    def get_all_configs(self) -> dict[str, Any]:
        """Get all configurations.

        Returns:
            All configurations
        """
        configs = self.repository.get_all_configs()
        return {
            c.key: c.get_typed_value() for c in configs
        }

    def validate_config(self, key: str, value: Any) -> bool:
        """Validate configuration value.

        Args:
            key: Configuration key
            value: Value to validate

        Returns:
            True if valid
        """
        config = self.repository.get_config(key)
        if not config or not config.validation_rules:
            return True

        rules = config.validation_rules
        str_value = str(value)

        # Check pattern
        if "pattern" in rules:
            import re
            if not re.match(rules["pattern"], str_value):
                return False

        # Check min/max
        try:
            if config.config_type == "integer":
                num_value = int(value)
                if "min" in rules and num_value < rules["min"]:
                    return False
                if "max" in rules and num_value > rules["max"]:
                    return False
        except (ValueError, TypeError):
            return False

        return True

    def export_config(self) -> dict[str, Any]:
        """Export all configurations.

        Returns:
            All configurations with metadata
        """
        configs = self.repository.get_all_configs()
        return {
            c.key: {
                "value": c.get_typed_value() if not c.is_secret else "***",
                "type": c.config_type,
                "category": c.category,
                "description": c.description,
                "is_secret": c.is_secret,
            }
            for c in configs
        }

    def reset_to_defaults(self, category: str | None = None) -> dict[str, Any]:
        """Reset configurations to defaults.

        Args:
            category: Category to reset (all if None)

        Returns:
            Reset results
        """
        configs = self.repository.get_all_configs(category=category)
        reset_count = 0

        for config in configs:
            if config.default_value:
                config.value = config.default_value
                reset_count += 1

        self.session.commit()

        return {
            "reset_count": reset_count,
            "category": category,
        }
