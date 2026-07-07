"""Plugin loader for dynamic extension loading."""

import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PluginMetadata:
    """Plugin metadata."""

    name: str
    version: str
    author: str
    description: str
    entry_point: str
    min_app_version: str
    max_app_version: str | None = None
    dependencies: list[str] = None
    tags: list[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "entry_point": self.entry_point,
            "min_app_version": self.min_app_version,
            "max_app_version": self.max_app_version,
            "tags": self.tags or [],
        }


class PluginInterface:
    """Base interface for all plugins."""

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        raise NotImplementedError

    def initialize(self, context: dict) -> bool:
        """Initialize plugin with context."""
        raise NotImplementedError

    def shutdown(self) -> None:
        """Shutdown plugin."""
        pass

    def get_capabilities(self) -> list[str]:
        """Get list of capabilities provided by plugin."""
        return []


class PluginLoader:
    """Load and manage plugins dynamically."""

    def __init__(self, plugin_dirs: list[str] | None = None):
        """Initialize plugin loader.

        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugin_dirs = plugin_dirs or []
        self.loaded_plugins: dict[str, PluginInterface] = {}
        self.plugin_metadata: dict[str, PluginMetadata] = {}
        self.context: dict[str, Any] = {}

    def add_plugin_dir(self, path: str) -> None:
        """Add a plugin directory."""
        plugin_path = Path(path)
        if plugin_path.is_dir():
            self.plugin_dirs.append(str(plugin_path.absolute()))
            if str(plugin_path) not in sys.path:
                sys.path.insert(0, str(plugin_path))

    def set_context(self, context: dict) -> None:
        """Set context for plugin initialization."""
        self.context = context

    def discover_plugins(self) -> list[str]:
        """Discover available plugins.

        Returns:
            List of plugin names found
        """
        plugins = []

        for plugin_dir in self.plugin_dirs:
            plugin_path = Path(plugin_dir)
            if not plugin_path.is_dir():
                continue

            # Look for plugin.json files
            for manifest_file in plugin_path.glob("*/plugin.json"):
                try:
                    with open(manifest_file) as f:
                        manifest = json.load(f)
                        plugins.append(manifest.get("name"))
                except Exception:
                    continue

        return plugins

    def load_plugin(self, plugin_name: str, version: str | None = None) -> bool:
        """Load a plugin by name.

        Args:
            plugin_name: Name of plugin to load
            version: Specific version (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find plugin directory
            plugin_dir = None
            for dir_path in self.plugin_dirs:
                potential_path = Path(dir_path) / plugin_name
                if potential_path.is_dir():
                    plugin_dir = potential_path
                    break

            if not plugin_dir:
                return False

            # Load plugin.json manifest
            manifest_file = plugin_dir / "plugin.json"
            if not manifest_file.is_file():
                return False

            with open(manifest_file) as f:
                manifest = json.load(f)

            # Create metadata
            metadata = PluginMetadata(
                name=manifest.get("name"),
                version=manifest.get("version"),
                author=manifest.get("author"),
                description=manifest.get("description"),
                entry_point=manifest.get("entry_point"),
                min_app_version=manifest.get("min_app_version"),
                max_app_version=manifest.get("max_app_version"),
                dependencies=manifest.get("dependencies", []),
                tags=manifest.get("tags", []),
            )

            # Dynamically import plugin module
            entry_point = manifest.get("entry_point")  # e.g., "plugin_module:PluginClass"
            module_path, class_name = entry_point.split(":")

            # Add plugin directory to path if not there
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))

            # Import module
            spec = importlib.util.spec_from_file_location(
                module_path, plugin_dir / f"{module_path}.py"
            )
            if spec is None or spec.loader is None:
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get plugin class
            if not hasattr(module, class_name):
                return False

            plugin_class: type[PluginInterface] = getattr(module, class_name)

            # Verify it implements PluginInterface
            if not issubclass(plugin_class, PluginInterface):
                return False

            # Instantiate and initialize plugin
            plugin_instance = plugin_class()

            # Store metadata
            self.plugin_metadata[plugin_name] = metadata

            # Initialize plugin
            if not plugin_instance.initialize(self.context):
                return False

            # Store plugin
            self.loaded_plugins[plugin_name] = plugin_instance

            return True

        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {str(e)}")
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if successful
        """
        if plugin_name not in self.loaded_plugins:
            return False

        try:
            plugin = self.loaded_plugins[plugin_name]
            plugin.shutdown()
            del self.loaded_plugins[plugin_name]
            return True
        except Exception:
            return False

    def get_plugin(self, plugin_name: str) -> PluginInterface | None:
        """Get loaded plugin by name."""
        return self.loaded_plugins.get(plugin_name)

    def get_plugins_by_tag(self, tag: str) -> list[PluginInterface]:
        """Get all plugins with a specific tag."""
        result = []
        for name, plugin in self.loaded_plugins.items():
            if name in self.plugin_metadata:
                metadata = self.plugin_metadata[name]
                if tag in (metadata.tags or []):
                    result.append(plugin)
        return result

    def get_capabilities(self) -> dict[str, list[str]]:
        """Get all capabilities from loaded plugins.

        Returns:
            Dict mapping plugin name to list of capabilities
        """
        result = {}
        for name, plugin in self.loaded_plugins.items():
            result[name] = plugin.get_capabilities()
        return result

    def list_loaded_plugins(self) -> list[str]:
        """List all loaded plugins."""
        return list(self.loaded_plugins.keys())

    def get_plugin_info(self, plugin_name: str) -> dict | None:
        """Get plugin information."""
        if plugin_name not in self.plugin_metadata:
            return None

        metadata = self.plugin_metadata[plugin_name]
        return {
            **metadata.to_dict(),
            "loaded": plugin_name in self.loaded_plugins,
        }

    def shutdown_all(self) -> None:
        """Shutdown all loaded plugins."""
        for plugin in self.loaded_plugins.values():
            try:
                plugin.shutdown()
            except Exception:
                pass

        self.loaded_plugins.clear()


# Global plugin loader instance
_plugin_loader: PluginLoader | None = None


def get_plugin_loader() -> PluginLoader:
    """Get singleton plugin loader instance."""
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader()
    return _plugin_loader


def initialize_plugin_loader(plugin_dirs: list[str] | None = None) -> PluginLoader:
    """Initialize global plugin loader."""
    global _plugin_loader
    _plugin_loader = PluginLoader(plugin_dirs)
    return _plugin_loader
