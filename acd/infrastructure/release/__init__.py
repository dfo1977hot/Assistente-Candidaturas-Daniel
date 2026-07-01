"""Release management infrastructure layer."""

from acd.infrastructure.release.version_manager import (
    SemanticVersion,
    VersionManager,
)
from acd.infrastructure.release.plugin_loader import (
    PluginInterface,
    PluginMetadata,
    PluginLoader,
    get_plugin_loader,
    initialize_plugin_loader,
)
from acd.infrastructure.release.feature_flag_service import (
    FeatureFlagService,
    get_feature_flag_service,
    initialize_feature_flag_service,
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
