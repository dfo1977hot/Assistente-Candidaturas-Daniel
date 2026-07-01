"""Configuration provider for centralized settings management."""

import os
import json
from typing import Any
from abc import ABC, abstractmethod

from acd.domain.platform.configuration import Configuration


class ConfigurationSource(ABC):
    """Abstract base for configuration sources."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Configuration value
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        pass

    @abstractmethod
    def get_all(self) -> dict[str, Any]:
        """Get all configurations.

        Returns:
            All configurations
        """
        pass


class EnvironmentConfigurationSource(ConfigurationSource):
    """Configuration from environment variables."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get from environment."""
        return os.getenv(key.upper(), default)

    def set(self, key: str, value: Any) -> None:
        """Set in environment."""
        os.environ[key.upper()] = str(value)

    def get_all(self) -> dict[str, Any]:
        """Get all environment variables."""
        return dict(os.environ)


class DatabaseConfigurationSource(ConfigurationSource):
    """Configuration from database."""

    def __init__(self, session) -> None:
        """Initialize with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def get(self, key: str, default: Any = None) -> Any:
        """Get from database."""
        config = self.session.query(Configuration).filter(Configuration.key == key).first()
        if config:
            return config.get_typed_value()
        return default

    def set(self, key: str, value: Any) -> None:
        """Set in database."""
        config = self.session.query(Configuration).filter(Configuration.key == key).first()
        if config:
            config.value = str(value)
        else:
            config = Configuration(key=key, value=str(value))
            self.session.add(config)
        self.session.commit()

    def get_all(self) -> dict[str, Any]:
        """Get all from database."""
        configs = self.session.query(Configuration).all()
        return {c.key: c.get_typed_value() for c in configs}


class JsonFileConfigurationSource(ConfigurationSource):
    """Configuration from JSON file."""

    def __init__(self, file_path: str) -> None:
        """Initialize with file path.

        Args:
            file_path: Path to JSON configuration file
        """
        self.file_path = file_path
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                self._config = json.load(f)
        else:
            self._config = {}

    def _save(self) -> None:
        """Save configuration to file."""
        with open(self.file_path, 'w') as f:
            json.dump(self._config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get from file."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set in file."""
        self._config[key] = value
        self._save()

    def get_all(self) -> dict[str, Any]:
        """Get all from file."""
        return self._config.copy()


class ConfigurationProvider:
    """Central configuration provider with multiple sources."""

    def __init__(self) -> None:
        """Initialize provider."""
        self.sources: list[tuple[str, ConfigurationSource]] = []
        self._cache: dict[str, Any] = {}

    def add_source(self, name: str, source: ConfigurationSource) -> None:
        """Add configuration source.

        Args:
            name: Source name
            source: Configuration source
        """
        self.sources.append((name, source))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Searches sources in order of addition. Returns first match.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Configuration value
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        # Search sources in order
        for _name, source in self.sources:
            value = source.get(key)
            if value is not None:
                self._cache[key] = value
                return value

        return default

    def set(self, key: str, value: Any, source_name: str | None = None) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
            source_name: Specific source to update (first if not specified)
        """
        if source_name:
            for name, source in self.sources:
                if name == source_name:
                    source.set(key, value)
                    break
        else:
            if self.sources:
                self.sources[0][1].set(key, value)

        self._cache[key] = value

    def get_all(self) -> dict[str, Any]:
        """Get all configurations from all sources.

        Returns:
            Merged configuration dict
        """
        result = {}
        for _name, source in reversed(self.sources):
            result.update(source.get_all())
        return result

    def invalidate_cache(self) -> None:
        """Invalidate configuration cache."""
        self._cache.clear()

    def get_section(self, prefix: str) -> dict[str, Any]:
        """Get all configurations with specific prefix.

        Args:
            prefix: Configuration prefix

        Returns:
            Configurations matching prefix
        """
        all_configs = self.get_all()
        return {k: v for k, v in all_configs.items() if k.startswith(prefix)}


# Default provider instance
_provider: ConfigurationProvider | None = None


def get_provider() -> ConfigurationProvider:
    """Get global provider instance.

    Returns:
        Configuration provider
    """
    global _provider
    if _provider is None:
        _provider = ConfigurationProvider()
    return _provider


def configure_provider(provider: ConfigurationProvider) -> None:
    """Set global provider instance.

    Args:
        provider: Configuration provider to set
    """
    global _provider
    _provider = provider
