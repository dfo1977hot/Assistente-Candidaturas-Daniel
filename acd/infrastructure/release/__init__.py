"""Release management infrastructure layer."""

from acd.infrastructure.release.feature_flag_service import (
    FeatureFlagService,
    get_feature_flag_service,
    initialize_feature_flag_service,
)
from acd.infrastructure.release.plugin_loader import (
    PluginInterface,
    PluginLoader,
    PluginMetadata,
    get_plugin_loader,
    initialize_plugin_loader,
)
from acd.infrastructure.release.version_manager import (
    SemanticVersion,
    VersionManager,
)

__all__ = [
    "SemanticVersion",
    "VersionManager",
    "PluginInterface",
    "PluginMetadata",
    "PluginLoader",
    "get_plugin_loader",
    "initialize_plugin_loader",
    "FeatureFlagService",
    "get_feature_flag_service",
    "initialize_feature_flag_service",
]
