"""Platform infrastructure components."""

from acd.infrastructure.platform.configuration_provider import (
    ConfigurationProvider,
    ConfigurationSource,
    DatabaseConfigurationSource,
    EnvironmentConfigurationSource,
    JsonFileConfigurationSource,
    configure_provider,
    get_provider,
)
from acd.infrastructure.platform.health_check_registry import (
    DatabaseHealthCheck,
    FilesystemHealthCheck,
    HealthCheck,
    HealthCheckRegistry,
    MemoryHealthCheck,
    get_registry,
)
from acd.infrastructure.platform.logger import StructuredLogger
from acd.infrastructure.platform.metrics_collector import (
    MetricsCollector,
    get_collector,
)
from acd.infrastructure.platform.migration_service import (
    Migration,
    MigrationService,
    get_migration_service,
)

__all__ = [
    "StructuredLogger",
    "ConfigurationProvider",
    "ConfigurationSource",
    "EnvironmentConfigurationSource",
    "DatabaseConfigurationSource",
    "JsonFileConfigurationSource",
    "get_provider",
    "configure_provider",
    "MetricsCollector",
    "get_collector",
    "HealthCheckRegistry",
    "HealthCheck",
    "DatabaseHealthCheck",
    "FilesystemHealthCheck",
    "MemoryHealthCheck",
    "get_registry",
    "MigrationService",
    "Migration",
    "get_migration_service",
]
